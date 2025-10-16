#!/usr/bin/env node
/**
 * Variable Verification Script
 * Validates all variables and functions are properly defined and accessible
 */

const fs = require('fs');
const path = require('path');

console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║        ULTRA-FAST ARBITRAGE ENGINE - VARIABLE VERIFICATION     ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

let totalChecks = 0;
let passedChecks = 0;
let failedChecks = 0;

function check(name, condition, details = '') {
  totalChecks++;
  if (condition) {
    console.log(`✓ ${name}`);
    if (details) console.log(`  ${details}`);
    passedChecks++;
    return true;
  } else {
    console.log(`✗ ${name}`);
    if (details) console.log(`  ${details}`);
    failedChecks++;
    return false;
  }
}

function sectionHeader(title) {
  console.log(`\n${'─'.repeat(65)}`);
  console.log(`  ${title}`);
  console.log('─'.repeat(65));
}

// Check 1: Module Files Exist
sectionHeader('MODULE FILES');
check('index.ts exists', fs.existsSync('index.ts'));
check('test.js exists', fs.existsSync('test.js'));
check('package.json exists', fs.existsSync('package.json'));
check('tsconfig.json exists', fs.existsSync('tsconfig.json'));
check('native/Cargo.toml exists', fs.existsSync('native/Cargo.toml'));
check('native/src/lib.rs exists', fs.existsSync('native/src/lib.rs'));
check('native/src/math.rs exists', fs.existsSync('native/src/math.rs'));
check('.env exists', fs.existsSync('.env'));

// Check 2: Build Artifacts
sectionHeader('BUILD ARTIFACTS');
const distExists = fs.existsSync('dist');
check('dist/ directory exists', distExists);
if (distExists) {
  check('dist/index.js exists', fs.existsSync('dist/index.js'));
  check('dist/index.d.ts exists', fs.existsSync('dist/index.d.ts'));
}
const nativeModule = fs.existsSync('native/math_engine.node');
check('native/math_engine.node exists', nativeModule);
if (nativeModule) {
  const stats = fs.statSync('native/math_engine.node');
  check('native module size is reasonable', stats.size > 100000 && stats.size < 2000000,
    `Size: ${(stats.size / 1024).toFixed(0)} KB`);
}

// Check 3: TypeScript Interface Functions
sectionHeader('TYPESCRIPT INTERFACE');
const indexTs = fs.readFileSync('index.ts', 'utf8');
const functions = [
  'computeSlippage',
  'computeUniswapV3Slippage',
  'computeCurveSlippage',
  'computeBalancerSlippage',
  'computeAggregatorSlippage',
  'getOptimalTradeSize'
];
functions.forEach(fn => {
  check(`${fn} function exported`, indexTs.includes(`export function ${fn}`));
});

// Check 4: Function Parameters
sectionHeader('FUNCTION PARAMETERS');
const parameters = [
  'reserveIn: number',
  'reserveOut: number',
  'amountIn: number',
  'liquidity: number',
  'sqrtPrice: number',
  'balanceIn: number',
  'balanceOut: number',
  'amplification: number',
  'weightIn: number',
  'weightOut: number',
  'gasCost: number',
  'minProfit: number'
];
parameters.forEach(param => {
  check(`Parameter ${param.split(':')[0]} defined`, indexTs.includes(param));
});

// Check 5: Test Suite
sectionHeader('TEST SUITE');
const testJs = fs.readFileSync('test.js', 'utf8');
check('Test framework defined', testJs.includes('function test('));
check('Assert functions defined', testJs.includes('function assert('));
const testCount = (testJs.match(/test\('/g) || []).length;
check('All 10 test cases present', testCount === 10, `Found ${testCount} tests`);

// Check 6: Rust NAPI Bindings
sectionHeader('RUST NAPI BINDINGS');
const libRs = fs.readFileSync('native/src/lib.rs', 'utf8');
const rustBindings = [
  'compute_uniswap_v2_slippage',
  'compute_uniswap_v3_slippage',
  'compute_curve_slippage',
  'compute_balancer_slippage',
  'compute_aggregator_slippage',
  'optimal_trade_size'
];
rustBindings.forEach(fn => {
  check(`${fn} NAPI binding`, libRs.includes(`pub fn ${fn}`));
});

// Check 7: Rust Math Functions
sectionHeader('RUST MATH FUNCTIONS');
const mathRs = fs.readFileSync('native/src/math.rs', 'utf8');
const mathFunctions = [
  'compute_uniswap_v2_slippage',
  'compute_uniswap_v3_slippage',
  'compute_curve_slippage',
  'compute_balancer_slippage',
  'compute_aggregator_slippage',
  'optimal_trade_size'
];
mathFunctions.forEach(fn => {
  check(`${fn} implementation`, mathRs.includes(`pub fn ${fn}`));
});

// Check 8: Cargo Configuration
sectionHeader('CARGO CONFIGURATION');
const cargoToml = fs.readFileSync('native/Cargo.toml', 'utf8');
check('Package name is math_engine', cargoToml.includes('name = "math_engine"'));
check('Version is 1.0.0', cargoToml.includes('version = "1.0.0"'));
check('Edition is 2021', cargoToml.includes('edition = "2021"'));
check('LTO enabled', cargoToml.includes('lto = true'));
check('Optimization level 3', cargoToml.includes('opt-level = 3'));
check('Single codegen unit', cargoToml.includes('codegen-units = 1'));

// Check 9: Package Configuration
sectionHeader('PACKAGE CONFIGURATION');
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
check('Package name correct', packageJson.name === 'ultra-fast-arbitrage-engine');
check('Version 1.0.0', packageJson.version === '1.0.0');
check('Build script defined', packageJson.scripts.build === 'tsc');
check('Test script defined', packageJson.scripts.test === 'node test.js');
check('Build:all script defined', packageJson.scripts['build:all'] !== undefined);

// Check 10: Environment Variables
sectionHeader('ENVIRONMENT VARIABLES');
const envFile = fs.readFileSync('.env', 'utf8');
const requiredEnvVars = [
  'CHAIN_ID',
  'EXECUTOR_ADDRESS',
  'MULTI_CHAIN_ENABLED',
  'MIN_PROFIT_USD',
  'MAX_GAS_PRICE_GWEI',
  'SLIPPAGE_TOLERANCE'
];
requiredEnvVars.forEach(envVar => {
  check(`${envVar} defined`, envFile.includes(`${envVar}=`));
});
// Check for at least one enabled chain
const hasEnabledChain = envFile.includes('MAINNET=true');
check('At least one chain enabled', hasEnabledChain);

// Check 11: TypeScript Configuration
sectionHeader('TYPESCRIPT CONFIGURATION');
const tsconfig = JSON.parse(fs.readFileSync('tsconfig.json', 'utf8'));
check('Target is ES2020', tsconfig.compilerOptions.target === 'ES2020');
check('Module is commonjs', tsconfig.compilerOptions.module === 'commonjs');
check('Declaration enabled', tsconfig.compilerOptions.declaration === true);
check('Strict mode enabled', tsconfig.compilerOptions.strict === true);
check('Output directory is ./dist', tsconfig.compilerOptions.outDir === './dist');

// Check 12: Module Loading Test (if built)
if (distExists && nativeModule) {
  sectionHeader('MODULE LOADING TEST');
  try {
    const engine = require('./dist/index.js');
    check('Module loads successfully', true);
    check('computeSlippage is function', typeof engine.computeSlippage === 'function');
    check('computeUniswapV3Slippage is function', typeof engine.computeUniswapV3Slippage === 'function');
    check('computeCurveSlippage is function', typeof engine.computeCurveSlippage === 'function');
    check('computeBalancerSlippage is function', typeof engine.computeBalancerSlippage === 'function');
    check('computeAggregatorSlippage is function', typeof engine.computeAggregatorSlippage === 'function');
    check('getOptimalTradeSize is function', typeof engine.getOptimalTradeSize === 'function');

    // Quick functional test
    sectionHeader('FUNCTIONAL TEST');
    try {
      const slippage = engine.computeSlippage(1000000, 2000000, 10000);
      check('computeSlippage returns number', typeof slippage === 'number');
      check('computeSlippage returns valid value', slippage > 0 && slippage < 100);
      
      const optimalSize = engine.getOptimalTradeSize(1000000, 2000000, 100, 50);
      check('getOptimalTradeSize returns number', typeof optimalSize === 'number');
      check('getOptimalTradeSize returns non-negative', optimalSize >= 0);
    } catch (e) {
      check('Function execution', false, `Error: ${e.message}`);
    }
  } catch (e) {
    check('Module loads successfully', false, `Error: ${e.message}`);
  }
}

// Final Summary
console.log('\n' + '═'.repeat(65));
console.log('  VERIFICATION SUMMARY');
console.log('═'.repeat(65));
console.log(`Total checks:  ${totalChecks}`);
console.log(`Passed:        ${passedChecks} ✓`);
console.log(`Failed:        ${failedChecks} ${failedChecks > 0 ? '✗' : ''}`);
console.log('─'.repeat(65));

if (failedChecks === 0) {
  console.log('✓ ALL CHECKS PASSED - System fully verified!\n');
  process.exit(0);
} else {
  console.log(`✗ ${failedChecks} CHECK(S) FAILED - Review errors above\n`);
  process.exit(1);
}
