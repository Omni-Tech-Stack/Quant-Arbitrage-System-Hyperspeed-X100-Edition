#!/usr/bin/env node
/**
 * Comprehensive Module Verification and Test Validation Script
 * This script verifies and validates all module tests and displays
 * a complete checkpoint of the directory structure
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ANSI color codes for terminal output
const COLORS = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
};

// Configuration
const ROOT_DIR = __dirname;
const MODULES = [
  {
    name: 'Backend API',
    path: 'backend',
    testCommand: 'npm test',
    buildCommand: null,
    hasTests: true,
  },
  {
    name: 'Ultra-Fast Arbitrage Engine',
    path: 'ultra-fast-arbitrage-engine',
    testCommand: 'npm test',
    buildCommand: 'npm run build',
    hasTests: true,
  },
  {
    name: 'Frontend',
    path: 'frontend',
    testCommand: null,
    buildCommand: null,
    hasTests: false,
  },
];

// Helper functions
function log(message, color = COLORS.reset) {
  console.log(`${color}${message}${COLORS.reset}`);
}

function printHeader(title, char = '=') {
  const line = char.repeat(80);
  console.log(`\n${COLORS.bright}${COLORS.cyan}${line}${COLORS.reset}`);
  console.log(`${COLORS.bright}${COLORS.cyan}  ${title}${COLORS.reset}`);
  console.log(`${COLORS.bright}${COLORS.cyan}${line}${COLORS.reset}\n`);
}

function printSection(title) {
  console.log(`\n${COLORS.bright}${COLORS.blue}${title}${COLORS.reset}`);
  console.log(`${COLORS.blue}${'-'.repeat(80)}${COLORS.reset}`);
}

function printSuccess(message) {
  log(`✓ ${message}`, COLORS.green);
}

function printError(message) {
  log(`✗ ${message}`, COLORS.red);
}

function printWarning(message) {
  log(`⚠ ${message}`, COLORS.yellow);
}

function printInfo(message) {
  log(`ℹ ${message}`, COLORS.cyan);
}

/**
 * Display directory tree structure
 */
function displayDirectoryTree(dir, prefix = '', isLast = true, maxDepth = 3, currentDepth = 0) {
  if (currentDepth >= maxDepth) return;

  const items = fs.readdirSync(dir, { withFileTypes: true });
  
  // Filter out node_modules, .git, and other common excludes
  const filteredItems = items.filter(item => {
    const name = item.name;
    return !name.startsWith('.') && 
           name !== 'node_modules' && 
           name !== 'dist' &&
           name !== 'target' &&
           name !== 'build';
  });

  filteredItems.forEach((item, index) => {
    const isLastItem = index === filteredItems.length - 1;
    const connector = isLastItem ? '└── ' : '├── ';
    const itemPath = path.join(dir, item.name);
    
    // Color code based on type
    let displayName = item.name;
    if (item.isDirectory()) {
      displayName = `${COLORS.blue}${item.name}/${COLORS.reset}`;
    } else if (item.name.endsWith('.js') || item.name.endsWith('.ts')) {
      displayName = `${COLORS.green}${item.name}${COLORS.reset}`;
    } else if (item.name.endsWith('.json')) {
      displayName = `${COLORS.yellow}${item.name}${COLORS.reset}`;
    } else if (item.name.endsWith('.md')) {
      displayName = `${COLORS.cyan}${item.name}${COLORS.reset}`;
    }

    console.log(`${prefix}${connector}${displayName}`);

    if (item.isDirectory()) {
      const newPrefix = prefix + (isLastItem ? '    ' : '│   ');
      displayDirectoryTree(itemPath, newPrefix, isLastItem, maxDepth, currentDepth + 1);
    }
  });
}

/**
 * Count files by extension
 */
function countFilesByExtension(dir, extensions = ['.js', '.ts', '.json', '.md', '.py']) {
  const counts = {};
  extensions.forEach(ext => counts[ext] = 0);

  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir, { withFileTypes: true });
    
    items.forEach(item => {
      const itemPath = path.join(currentDir, item.name);
      
      if (item.isDirectory() && 
          item.name !== 'node_modules' && 
          !item.name.startsWith('.') &&
          item.name !== 'dist' &&
          item.name !== 'target') {
        traverse(itemPath);
      } else if (item.isFile()) {
        const ext = path.extname(item.name);
        if (ext in counts) {
          counts[ext]++;
        }
      }
    });
  }

  traverse(dir);
  return counts;
}

/**
 * Find all test files in the repository
 */
function findTestFiles(dir) {
  const testFiles = [];

  function traverse(currentDir) {
    const items = fs.readdirSync(currentDir, { withFileTypes: true });
    
    items.forEach(item => {
      const itemPath = path.join(currentDir, item.name);
      
      if (item.isDirectory() && 
          item.name !== 'node_modules' && 
          !item.name.startsWith('.') &&
          item.name !== 'dist' &&
          item.name !== 'target') {
        traverse(itemPath);
      } else if (item.isFile() && 
                 (item.name.includes('test') || item.name.includes('spec'))) {
        testFiles.push(path.relative(dir, itemPath));
      }
    });
  }

  traverse(dir);
  return testFiles;
}

/**
 * Run tests for a module
 */
function runModuleTests(module) {
  const modulePath = path.join(ROOT_DIR, module.path);
  
  printSection(`Testing: ${module.name}`);
  
  if (!fs.existsSync(modulePath)) {
    printError(`Module directory not found: ${module.path}`);
    return { success: false, error: 'Directory not found' };
  }

  if (!module.hasTests || !module.testCommand) {
    printWarning('No tests configured for this module');
    return { success: true, skipped: true };
  }

  try {
    // Build if necessary
    if (module.buildCommand) {
      printInfo(`Building module...`);
      execSync(module.buildCommand, { 
        cwd: modulePath, 
        stdio: 'inherit',
        timeout: 180000 
      });
      printSuccess('Build completed');
    }

    // Run tests
    printInfo(`Running tests...`);
    const output = execSync(module.testCommand, { 
      cwd: modulePath, 
      encoding: 'utf-8',
      timeout: 180000 
    });
    
    printSuccess('All tests passed');
    return { success: true, output };
  } catch (error) {
    printError(`Tests failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

/**
 * Generate module statistics
 */
function generateModuleStats(module) {
  const modulePath = path.join(ROOT_DIR, module.path);
  
  if (!fs.existsSync(modulePath)) {
    return null;
  }

  const fileCounts = countFilesByExtension(modulePath);
  const testFiles = findTestFiles(modulePath);
  
  return {
    name: module.name,
    path: module.path,
    fileCounts,
    testFiles,
    testFileCount: testFiles.length,
  };
}

/**
 * Main verification process
 */
async function main() {
  printHeader('COMPREHENSIVE MODULE VERIFICATION & TEST VALIDATION');
  
  log(`${COLORS.bright}Repository:${COLORS.reset} Quant-Arbitrage-System-Hyperspeed-X100-Edition`);
  log(`${COLORS.bright}Root Directory:${COLORS.reset} ${ROOT_DIR}`);
  log(`${COLORS.bright}Date:${COLORS.reset} ${new Date().toISOString()}\n`);

  // CHECKPOINT 1: Directory Structure
  printHeader('CHECKPOINT 1: DIRECTORY STRUCTURE', '=');
  printSection('Repository Tree (3 levels deep)');
  displayDirectoryTree(ROOT_DIR);

  // CHECKPOINT 2: File Statistics
  printHeader('CHECKPOINT 2: FILE STATISTICS', '=');
  const totalCounts = countFilesByExtension(ROOT_DIR);
  
  console.log('\n' + COLORS.bright + 'File Counts by Extension:' + COLORS.reset);
  console.log('─'.repeat(40));
  Object.entries(totalCounts).forEach(([ext, count]) => {
    const label = ext.padEnd(15);
    const countStr = count.toString().padStart(5);
    console.log(`  ${label} ${countStr}`);
  });
  console.log('─'.repeat(40));

  // CHECKPOINT 3: Test File Discovery
  printHeader('CHECKPOINT 3: TEST FILE DISCOVERY', '=');
  const allTestFiles = findTestFiles(ROOT_DIR);
  
  console.log(`\n${COLORS.bright}Total Test Files Found: ${allTestFiles.length}${COLORS.reset}\n`);
  
  allTestFiles.forEach(file => {
    console.log(`  ${COLORS.green}✓${COLORS.reset} ${file}`);
  });

  // CHECKPOINT 4: Module Statistics
  printHeader('CHECKPOINT 4: MODULE STATISTICS', '=');
  
  const moduleStats = MODULES.map(generateModuleStats).filter(s => s !== null);
  
  console.log('\n' + COLORS.bright + 'Module Overview:' + COLORS.reset);
  console.log('─'.repeat(80));
  console.log(`${'Module'.padEnd(35)} ${'Test Files'.padStart(12)} ${'JS/TS'.padStart(10)}`);
  console.log('─'.repeat(80));
  
  moduleStats.forEach(stats => {
    const moduleName = stats.name.padEnd(35);
    const testCount = stats.testFileCount.toString().padStart(12);
    const jsCount = ((stats.fileCounts['.js'] || 0) + (stats.fileCounts['.ts'] || 0)).toString().padStart(10);
    console.log(`${moduleName} ${testCount} ${jsCount}`);
  });
  console.log('─'.repeat(80));

  // CHECKPOINT 5: Test Execution
  printHeader('CHECKPOINT 5: TEST EXECUTION & VALIDATION', '=');
  
  const testResults = [];
  
  for (const module of MODULES) {
    const result = runModuleTests(module);
    testResults.push({
      module: module.name,
      ...result,
    });
  }

  // CHECKPOINT 6: Final Summary
  printHeader('CHECKPOINT 6: VALIDATION SUMMARY', '=');
  
  console.log('\n' + COLORS.bright + 'Test Results Summary:' + COLORS.reset);
  console.log('─'.repeat(80));
  console.log(`${'Module'.padEnd(40)} ${'Status'.padStart(20)}`);
  console.log('─'.repeat(80));
  
  let totalPassed = 0;
  let totalFailed = 0;
  let totalSkipped = 0;
  
  testResults.forEach(result => {
    const moduleName = result.module.padEnd(40);
    let status;
    
    if (result.skipped) {
      status = `${COLORS.yellow}SKIPPED (No Tests)${COLORS.reset}`;
      totalSkipped++;
    } else if (result.success) {
      status = `${COLORS.green}✓ PASSED${COLORS.reset}`;
      totalPassed++;
    } else {
      status = `${COLORS.red}✗ FAILED${COLORS.reset}`;
      totalFailed++;
    }
    
    console.log(`${moduleName} ${status.padStart(20)}`);
  });
  
  console.log('─'.repeat(80));
  console.log(`\nTotal Modules: ${testResults.length}`);
  console.log(`${COLORS.green}Passed: ${totalPassed}${COLORS.reset}`);
  console.log(`${COLORS.red}Failed: ${totalFailed}${COLORS.reset}`);
  console.log(`${COLORS.yellow}Skipped: ${totalSkipped}${COLORS.reset}`);
  
  // Final Status
  console.log('\n' + '='.repeat(80));
  if (totalFailed === 0) {
    log(`\n✓ ${COLORS.bright}ALL VALIDATIONS PASSED - SYSTEM VERIFIED!${COLORS.reset}\n`, COLORS.green);
  } else {
    log(`\n✗ ${COLORS.bright}VALIDATION FAILED - ${totalFailed} MODULE(S) FAILED${COLORS.reset}\n`, COLORS.red);
  }
  console.log('='.repeat(80) + '\n');

  // Generate JSON report
  const report = {
    timestamp: new Date().toISOString(),
    repository: 'Quant-Arbitrage-System-Hyperspeed-X100-Edition',
    totalModules: MODULES.length,
    fileStatistics: totalCounts,
    totalTestFiles: allTestFiles.length,
    testFiles: allTestFiles,
    moduleStatistics: moduleStats,
    testResults: testResults,
    summary: {
      passed: totalPassed,
      failed: totalFailed,
      skipped: totalSkipped,
      successRate: totalPassed / (totalPassed + totalFailed) * 100 || 0,
    },
  };

  const reportPath = path.join(ROOT_DIR, 'MODULE_VERIFICATION_REPORT.json');
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
  printInfo(`\nDetailed report saved to: ${reportPath}`);

  // Exit with appropriate code
  process.exit(totalFailed > 0 ? 1 : 0);
}

// Run the verification
main().catch(error => {
  printError(`\nFatal error: ${error.message}`);
  console.error(error);
  process.exit(1);
});
