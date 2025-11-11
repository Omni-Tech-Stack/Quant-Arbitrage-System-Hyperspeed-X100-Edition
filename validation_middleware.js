#!/usr/bin/env node
/**
 * VALIDATION MIDDLEWARE
 * JavaScript/Node.js middleware for data validation with 4-layer fallback
 * Used by dex_pool_fetcher.js and sdk_pool_loader.js
 */

const fs = require('fs');
const path = require('path');

/**
 * Data Source Types (matches Python DataSource enum)
 */
const DataSource = {
  // Layer 1: Primary SDK Sources
  UNISWAP_SDK: 'uniswap_sdk',
  BALANCER_SDK: 'balancer_sdk',
  CURVE_SDK: 'curve_sdk',
  DIRECT_CONTRACT: 'direct_contract',
  SUBGRAPH: 'subgraph',
  
  // Layer 2: RPC Endpoints
  ALCHEMY_RPC: 'alchemy_rpc',
  INFURA_RPC: 'infura_rpc',
  QUICKNODE_RPC: 'quicknode_rpc',
  PUBLIC_RPC: 'public_rpc',
  
  // Layer 3: Aggregated/Cached
  LOCAL_CACHE: 'local_cache',
  AGGREGATED: 'aggregated',
  HISTORICAL_BASELINE: 'historical_baseline',
  
  // Layer 4: Emergency Fallbacks
  LAST_KNOWN_GOOD: 'last_known_good',
  CONSERVATIVE_ESTIMATE: 'conservative_estimate',
  SAFE_DEFAULT: 'safe_default',
  
  UNKNOWN: 'unknown'
};

/**
 * Validation Status
 */
const ValidationStatus = {
  UNVALIDATED: 'unvalidated',
  VALIDATED: 'validated',
  FLAGGED: 'flagged',
  REJECTED: 'rejected'
};

/**
 * Data Point Class (matches Python DataPoint)
 */
class DataPoint {
  constructor({
    value,
    dataType,
    source,
    layer,
    validationStatus = ValidationStatus.UNVALIDATED,
    oracleVerified = false,
    oracleSource = null,
    oracleDeviation = null,
    staleness = 0.0,
    confidence = 0.0,
    metadata = {},
    requestId = null,
    chain = null,
    token = null
  }) {
    this.value = value;
    this.dataType = dataType;
    this.source = source;
    this.layer = layer;
    this.timestamp = Date.now() / 1000; // Unix timestamp in seconds
    this.validationStatus = validationStatus;
    this.oracleVerified = oracleVerified;
    this.oracleSource = oracleSource;
    this.oracleDeviation = oracleDeviation;
    this.staleness = staleness;
    this.confidence = confidence || this.calculateConfidence();
    this.metadata = metadata;
    this.requestId = requestId || `${dataType}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.chain = chain;
    this.token = token;
  }

  /**
   * Calculate confidence score based on source, freshness, and oracle verification
   */
  calculateConfidence() {
    // Source weights based on layer
    const sourceWeights = {
      1: 1.0,   // Layer 1: SDK/Direct
      2: 0.95,  // Layer 2: RPC
      3: 0.85,  // Layer 3: Aggregated
      4: 0.60   // Layer 4: Cached/Fallback
    };
    const sourceWeight = sourceWeights[this.layer] || 0.5;

    // Freshness weight
    let freshnessWeight;
    if (this.staleness < 5) {
      freshnessWeight = 1.0;
    } else if (this.staleness < 12) {
      freshnessWeight = 0.95;
    } else if (this.staleness < 30) {
      freshnessWeight = 0.85;
    } else if (this.staleness < 60) {
      freshnessWeight = 0.70;
    } else {
      freshnessWeight = 0.50;
    }

    // Oracle verification weight
    let oracleWeight;
    if (this.oracleVerified) {
      if (this.oracleDeviation !== null && this.oracleDeviation < 0.02) {
        oracleWeight = 1.0;
      } else if (this.oracleDeviation !== null && this.oracleDeviation < 0.05) {
        oracleWeight = 0.85;
      } else {
        oracleWeight = 0.50;
      }
    } else {
      oracleWeight = 0.80; // Not verified
    }

    // Combined confidence
    return parseFloat((sourceWeight * freshnessWeight * oracleWeight).toFixed(4));
  }

  /**
   * Update staleness and recalculate confidence
   */
  updateStaleness() {
    this.staleness = (Date.now() / 1000) - this.timestamp;
    this.confidence = this.calculateConfidence();
  }

  /**
   * Check if data is stale beyond threshold
   */
  isStale(maxAgeSeconds) {
    this.updateStaleness();
    return this.staleness > maxAgeSeconds;
  }

  /**
   * Convert to plain object
   */
  toObject() {
    return {
      value: this.value,
      dataType: this.dataType,
      source: this.source,
      layer: this.layer,
      timestamp: this.timestamp,
      validationStatus: this.validationStatus,
      oracleVerified: this.oracleVerified,
      oracleSource: this.oracleSource,
      oracleDeviation: this.oracleDeviation,
      staleness: this.staleness,
      confidence: this.confidence,
      metadata: this.metadata,
      requestId: this.requestId,
      chain: this.chain,
      token: this.token
    };
  }
}

/**
 * Validation Middleware
 */
class ValidationMiddleware {
  constructor(options = {}) {
    this.stalenessLimits = options.stalenessLimits || {
      price: 12,      // 1 Polygon block
      gas: 12,        // 1 block
      liquidity: 60,  // 5 blocks
      pool_data: 300, // 25 blocks
      default: 30
    };

    this.minConfidence = options.minConfidence || {
      price: 0.85,
      gas: 0.85,
      liquidity: 0.80,
      pool_data: 0.75,
      default: 0.75
    };

    // In-memory data tracking
    this.dataPoints = new Map(); // requestId -> DataPoint
    this.unaccountedData = [];
    this.flaggedData = [];

    // Statistics
    this.stats = {
      totalTracked: 0,
      totalValidated: 0,
      totalRejected: 0,
      totalUnaccounted: 0,
      layerUsage: { 1: 0, 2: 0, 3: 0, 4: 0 }
    };

    console.log('[ValidationMiddleware] ✓ Initialized');
  }

  /**
   * Record a data point
   */
  record(dataPoint) {
    if (!(dataPoint instanceof DataPoint)) {
      throw new Error('Must provide a DataPoint instance');
    }

    // Update staleness and confidence
    dataPoint.updateStaleness();

    // Store
    this.dataPoints.set(dataPoint.requestId, dataPoint);

    // Update statistics
    this.stats.totalTracked++;
    this.stats.layerUsage[dataPoint.layer] = (this.stats.layerUsage[dataPoint.layer] || 0) + 1;

    if (dataPoint.validationStatus === ValidationStatus.VALIDATED) {
      this.stats.totalValidated++;
    } else if (dataPoint.validationStatus === ValidationStatus.UNVALIDATED) {
      this.unaccountedData.push(dataPoint.requestId);
      this.stats.totalUnaccounted++;
    } else if (dataPoint.validationStatus === ValidationStatus.FLAGGED) {
      this.flaggedData.push(dataPoint.requestId);
    }

    console.log(
      `[ValidationMiddleware] Recorded ${dataPoint.dataType} from ${dataPoint.source} ` +
      `(confidence: ${dataPoint.confidence.toFixed(2)})`
    );

    return dataPoint.requestId;
  }

  /**
   * Validate a data point
   */
  validate(requestId, oracleVerified = false, oracleSource = null, oracleDeviation = null) {
    const dataPoint = this.dataPoints.get(requestId);
    if (!dataPoint) {
      console.error(`[ValidationMiddleware] Cannot validate unknown requestId: ${requestId}`);
      return false;
    }

    // Update validation status
    dataPoint.validationStatus = ValidationStatus.VALIDATED;
    dataPoint.oracleVerified = oracleVerified;
    dataPoint.oracleSource = oracleSource;
    dataPoint.oracleDeviation = oracleDeviation;

    // Recalculate confidence
    dataPoint.updateStaleness();

    // Flag if oracle deviation is high
    if (oracleDeviation !== null && oracleDeviation > 0.05) {
      dataPoint.validationStatus = ValidationStatus.FLAGGED;
      if (!this.flaggedData.includes(requestId)) {
        this.flaggedData.push(requestId);
      }
      console.warn(
        `[ValidationMiddleware] Flagged ${requestId}: oracle deviation ${(oracleDeviation * 100).toFixed(2)}%`
      );
    }

    // Remove from unaccounted if present
    const unaccountedIndex = this.unaccountedData.indexOf(requestId);
    if (unaccountedIndex > -1) {
      this.unaccountedData.splice(unaccountedIndex, 1);
      this.stats.totalUnaccounted--;
    }

    this.stats.totalValidated++;

    console.log(
      `[ValidationMiddleware] Validated ${requestId} ` +
      `(oracle: ${oracleVerified}, confidence: ${dataPoint.confidence.toFixed(2)})`
    );

    return true;
  }

  /**
   * Reject a data point
   */
  reject(requestId, reason) {
    const dataPoint = this.dataPoints.get(requestId);
    if (!dataPoint) {
      console.error(`[ValidationMiddleware] Cannot reject unknown requestId: ${requestId}`);
      return false;
    }

    dataPoint.validationStatus = ValidationStatus.REJECTED;
    dataPoint.metadata.rejectionReason = reason;

    this.stats.totalRejected++;

    console.log(`[ValidationMiddleware] Rejected ${requestId}: ${reason}`);

    return true;
  }

  /**
   * Get a data point by requestId
   */
  getDataPoint(requestId) {
    return this.dataPoints.get(requestId);
  }

  /**
   * Check if data requires double-validation
   */
  requiresDoubleValidation(requestId) {
    if (this.unaccountedData.includes(requestId)) {
      return true;
    }

    if (this.flaggedData.includes(requestId)) {
      return true;
    }

    const dataPoint = this.getDataPoint(requestId);
    if (!dataPoint) {
      return true; // Unknown data always requires double-validation
    }

    const maxAge = this.stalenessLimits[dataPoint.dataType] || this.stalenessLimits.default;
    if (dataPoint.isStale(maxAge)) {
      return true;
    }

    const minConf = this.minConfidence[dataPoint.dataType] || this.minConfidence.default;
    if (dataPoint.confidence < minConf) {
      return true;
    }

    return false;
  }

  /**
   * Get statistics
   */
  getStatistics() {
    const total = Math.max(this.stats.totalTracked, 1);

    return {
      totalTracked: this.stats.totalTracked,
      totalValidated: this.stats.totalValidated,
      totalRejected: this.stats.totalRejected,
      totalUnaccounted: this.stats.totalUnaccounted,
      validationRate: parseFloat((this.stats.totalValidated / total).toFixed(4)),
      rejectionRate: parseFloat((this.stats.totalRejected / total).toFixed(4)),
      unaccountedRate: parseFloat((this.stats.totalUnaccounted / total).toFixed(4)),
      layerUsage: this.stats.layerUsage,
      layer1Pct: parseFloat((this.stats.layerUsage[1] / total * 100).toFixed(2)),
      layer2Pct: parseFloat((this.stats.layerUsage[2] / total * 100).toFixed(2)),
      layer3Pct: parseFloat((this.stats.layerUsage[3] / total * 100).toFixed(2)),
      layer4Pct: parseFloat((this.stats.layerUsage[4] / total * 100).toFixed(2)),
      flaggedCount: this.flaggedData.length
    };
  }

  /**
   * Print statistics
   */
  printStatistics() {
    const stats = this.getStatistics();

    console.log('\n' + '='.repeat(80));
    console.log('  VALIDATION MIDDLEWARE STATISTICS');
    console.log('='.repeat(80));
    console.log(`Total Tracked:    ${stats.totalTracked}`);
    console.log(`Validated:        ${stats.totalValidated} (${(stats.validationRate * 100).toFixed(1)}%)`);
    console.log(`Rejected:         ${stats.totalRejected} (${(stats.rejectionRate * 100).toFixed(1)}%)`);
    console.log(`Unaccounted:      ${stats.totalUnaccounted} (${(stats.unaccountedRate * 100).toFixed(1)}%)`);
    console.log(`Flagged:          ${stats.flaggedCount}`);
    console.log(`\nLayer Usage:`);
    console.log(`  Layer 1 (SDK):        ${stats.layer1Pct}%`);
    console.log(`  Layer 2 (RPC):        ${stats.layer2Pct}%`);
    console.log(`  Layer 3 (Aggregated): ${stats.layer3Pct}%`);
    console.log(`  Layer 4 (Fallback):   ${stats.layer4Pct}%`);
    console.log('='.repeat(80) + '\n');
  }

  /**
   * Export to JSON file
   */
  exportToJSON(filepath) {
    const data = {
      statistics: this.getStatistics(),
      dataPoints: Array.from(this.dataPoints.values()).map(dp => dp.toObject()),
      timestamp: new Date().toISOString()
    };

    fs.writeFileSync(filepath, JSON.stringify(data, null, 2));
    console.log(`[ValidationMiddleware] Exported ${this.dataPoints.size} data points to ${filepath}`);
  }
}

/**
 * Singleton instance
 */
let middlewareInstance = null;

function getMiddleware(options) {
  if (!middlewareInstance) {
    middlewareInstance = new ValidationMiddleware(options);
  }
  return middlewareInstance;
}

// Export
module.exports = {
  DataSource,
  ValidationStatus,
  DataPoint,
  ValidationMiddleware,
  getMiddleware
};

// Example usage if run directly
if (require.main === module) {
  const middleware = new ValidationMiddleware();

  // Create a data point
  const priceData = new DataPoint({
    value: 1850.50,
    dataType: 'price',
    source: DataSource.UNISWAP_SDK,
    layer: 1,
    chain: 'polygon',
    token: 'WETH',
    metadata: { pair: 'WETH/USDC' }
  });

  // Record and validate
  const requestId = middleware.record(priceData);
  middleware.validate(requestId, true, 'chainlink', 0.01);

  // Simulate more data
  for (let i = 0; i < 10; i++) {
    const gasData = new DataPoint({
      value: 100 + i,
      dataType: 'gas',
      source: i % 2 === 0 ? DataSource.ALCHEMY_RPC : DataSource.INFURA_RPC,
      layer: 2,
      chain: 'polygon'
    });

    const rid = middleware.record(gasData);
    if (i % 3 === 0) {
      middleware.validate(rid);
    }
  }

  // Print statistics
  middleware.printStatistics();
}
