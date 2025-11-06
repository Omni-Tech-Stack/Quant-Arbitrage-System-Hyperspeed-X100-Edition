#!/usr/bin/env node
/**
 * Comprehensive .env Variable Analysis Script
 * Analyzes all environment variables and checks their implementation in the system
 */

const fs = require('fs');
const path = require('path');

console.log('╔═══════════════════════════════════════════════════════════════╗');
console.log('║         ENVIRONMENT VARIABLE ANALYSIS & IMPLEMENTATION        ║');
console.log('╚═══════════════════════════════════════════════════════════════╝\n');

// Read .env file
const envPath = path.join(__dirname, 'ultra-fast-arbitrage-engine', '.env');
const envContent = fs.readFileSync(envPath, 'utf8');

// Extract all environment variables
const envVars = new Map();
const lines = envContent.split('\n');

for (const line of lines) {
  // Match patterns like: VAR_NAME=value or ## VAR_NAME=value
  const match = line.match(/^#*\s*([A-Z][A-Z0-9_]*)\s*=/);
  if (match) {
    const varName = match[1].replace(/\\_/g, '_'); // Unescape underscores
    if (!envVars.has(varName)) {
      envVars.set(varName, {
        name: varName,
        value: line.split('=')[1] || '',
        line: line,
        usedIn: [],
        implemented: false
      });
    }
  }
}

console.log(`Found ${envVars.size} unique environment variables in .env file\n`);

// Search for usage in codebase
const searchDirs = [
  'ultra-fast-arbitrage-engine',
  'backend',
  'src',
  'config',
  'scripts',
  'tests',
  '.'
];

const extensions = ['.js', '.ts', '.py', '.json'];

function searchInFile(filePath, varName) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const patterns = [
      new RegExp(`process\\.env\\.${varName}`, 'g'),
      new RegExp(`os\\.getenv\\(['"]${varName}['"]\\)`, 'g'),
      new RegExp(`os\\.environ\\['${varName}'\\]`, 'g'),
      new RegExp(`['"]${varName}['"]`, 'g'),
      new RegExp(`${varName}`, 'g')
    ];
    
    for (const pattern of patterns) {
      if (pattern.test(content)) {
        return true;
      }
    }
  } catch (e) {
    // Ignore read errors
  }
  return false;
}

function getAllFiles(dir, fileList = []) {
  if (!fs.existsSync(dir)) return fileList;
  
  try {
    const files = fs.readdirSync(dir);
    
    for (const file of files) {
      const filePath = path.join(dir, file);
      try {
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          if (!file.startsWith('.') && 
              file !== 'node_modules' && 
              file !== 'dist' &&
              file !== 'logs' &&
              file !== 'models') {
            getAllFiles(filePath, fileList);
          }
        } else {
          const ext = path.extname(file);
          if (extensions.includes(ext)) {
            fileList.push(filePath);
          }
        }
      } catch (e) {
        // Ignore stat errors
      }
    }
  } catch (e) {
    // Ignore read errors
  }
  
  return fileList;
}

// Get all relevant files
const allFiles = [];
for (const dir of searchDirs) {
  const dirPath = path.join(__dirname, dir);
  getAllFiles(dirPath, allFiles);
}

console.log(`Scanning ${allFiles.length} files for variable usage...\n`);

// Check each variable
for (const [varName, varData] of envVars) {
  for (const file of allFiles) {
    if (searchInFile(file, varName)) {
      const relativePath = path.relative(__dirname, file);
      if (!varData.usedIn.includes(relativePath)) {
        varData.usedIn.push(relativePath);
      }
    }
  }
  
  if (varData.usedIn.length > 0) {
    varData.implemented = true;
  }
}

// Categorize variables
const categories = {
  'Network & Chain Configuration': [],
  'Wallet & Execution': [],
  'DEX Protocol Endpoints': [],
  'MEV & Flashloan': [],
  'Database & Redis': [],
  'Telegram & Notifications': [],
  'ML & AI Configuration': [],
  'Execution & Risk Parameters': [],
  'Monitoring & Logging': [],
  'Swarm Configuration': [],
  'Chain Endpoints': [],
  'Uncategorized': []
};

for (const [varName, varData] of envVars) {
  if (varName.includes('MAINNET') || varName.includes('TESTNET') || varName.includes('SEPOLIA') ||
      varName.includes('HTTPS') || varName.includes('WSS') || varName.includes('INFURA') ||
      varName.includes('ALCHEMY') || varName.includes('QUICKNODE') || varName.includes('FUJI') ||
      varName.includes('ALFAJORES') || varName.includes('AMOY') || varName.includes('HOODI')) {
    categories['Chain Endpoints'].push(varData);
  } else if (varName.startsWith('CHAIN_ID') || varName === 'MULTI_CHAIN_ENABLED') {
    categories['Network & Chain Configuration'].push(varData);
  } else if (varName.includes('EXECUTOR') || varName.includes('PRIVATE_KEY')) {
    categories['Wallet & Execution'].push(varData);
  } else if (varName.includes('UNISWAP') || varName.includes('SUSHISWAP') || varName.includes('QUICKSWAP') ||
             varName.includes('CURVE') || varName.includes('BALANCER') || varName.includes('AAVE') ||
             varName.includes('DODO')) {
    categories['DEX Protocol Endpoints'].push(varData);
  } else if (varName.includes('FLASHBOTS') || varName.includes('BLOXROUTE') || varName.includes('MERKLE') ||
             varName.includes('EDEN') || varName.includes('MEV') || varName.includes('MEMPOOL')) {
    categories['MEV & Flashloan'].push(varData);
  } else if (varName.includes('POSTGRES') || varName.includes('REDIS')) {
    categories['Database & Redis'].push(varData);
  } else if (varName.includes('TELEGRAM') || varName.includes('DISCORD')) {
    categories['Telegram & Notifications'].push(varData);
  } else if (varName.includes('ML_') || varName.includes('TAR_')) {
    categories['ML & AI Configuration'].push(varData);
  } else if (varName.includes('MIN_') || varName.includes('MAX_') || varName.includes('SLIPPAGE') ||
             varName.includes('SIMULATION') || varName.includes('BLACKLIST')) {
    categories['Execution & Risk Parameters'].push(varData);
  } else if (varName.includes('LOG_') || varName.includes('PROMETHEUS') || varName.includes('HEALTH') ||
             varName.includes('METRICS')) {
    categories['Monitoring & Logging'].push(varData);
  } else if (varName.includes('SWARM_')) {
    categories['Swarm Configuration'].push(varData);
  } else {
    categories['Uncategorized'].push(varData);
  }
}

// Print results
const notImplemented = [];

for (const [category, vars] of Object.entries(categories)) {
  if (vars.length === 0) continue;
  
  console.log(`\n${'═'.repeat(75)}`);
  console.log(`  ${category.toUpperCase()}`);
  console.log('═'.repeat(75));
  
  for (const varData of vars) {
    const status = varData.implemented ? '✓' : '✗';
    const statusText = varData.implemented ? 'IMPLEMENTED' : 'NOT IMPLEMENTED';
    console.log(`\n${status} ${varData.name} - ${statusText}`);
    
    if (varData.implemented) {
      console.log(`  Used in ${varData.usedIn.length} file(s):`);
      varData.usedIn.slice(0, 3).forEach(file => {
        console.log(`    - ${file}`);
      });
      if (varData.usedIn.length > 3) {
        console.log(`    ... and ${varData.usedIn.length - 3} more`);
      }
    } else {
      notImplemented.push(varData);
    }
  }
}

// Summary
console.log('\n\n' + '═'.repeat(75));
console.log('  IMPLEMENTATION SUMMARY');
console.log('═'.repeat(75));

const totalVars = envVars.size;
const implementedVars = Array.from(envVars.values()).filter(v => v.implemented).length;
const notImplementedVars = totalVars - implementedVars;

console.log(`Total variables:          ${totalVars}`);
console.log(`Implemented:              ${implementedVars} ✓`);
console.log(`Not implemented:          ${notImplementedVars} ✗`);
console.log(`Implementation rate:      ${((implementedVars/totalVars) * 100).toFixed(1)}%`);

if (notImplemented.length > 0) {
  console.log('\n' + '─'.repeat(75));
  console.log('  VARIABLES REQUIRING IMPLEMENTATION');
  console.log('─'.repeat(75));
  
  notImplemented.forEach((varData, index) => {
    console.log(`${index + 1}. ${varData.name}`);
  });
}

// Save detailed report
const report = {
  timestamp: new Date().toISOString(),
  totalVariables: totalVars,
  implementedCount: implementedVars,
  notImplementedCount: notImplementedVars,
  implementationRate: ((implementedVars/totalVars) * 100).toFixed(1) + '%',
  categories: {},
  notImplemented: notImplemented.map(v => ({
    name: v.name,
    value: v.value.substring(0, 50)
  }))
};

for (const [category, vars] of Object.entries(categories)) {
  if (vars.length > 0) {
    report.categories[category] = vars.map(v => ({
      name: v.name,
      implemented: v.implemented,
      usageCount: v.usedIn.length,
      files: v.usedIn
    }));
  }
}

fs.writeFileSync(
  path.join(__dirname, 'env-analysis-report.json'),
  JSON.stringify(report, null, 2)
);

console.log('\n✓ Detailed report saved to: env-analysis-report.json\n');

process.exit(notImplementedVars > 0 ? 1 : 0);
