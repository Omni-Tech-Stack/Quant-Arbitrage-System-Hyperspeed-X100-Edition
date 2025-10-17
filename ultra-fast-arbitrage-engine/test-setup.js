#!/usr/bin/env node
/**
 * Test script for setup.js
 * Validates that all setup components are in place
 */

const fs = require('fs');
const path = require('path');

console.log('Testing setup.js structure...\n');

let passed = 0;
let failed = 0;

function test(description, condition) {
  if (condition) {
    console.log(`✓ ${description}`);
    passed++;
  } else {
    console.error(`✗ ${description}`);
    failed++;
  }
}

// Test 1: Check if setup.js exists and is readable
test('setup.js exists', fs.existsSync('setup.js'));

// Test 2: Check for key functions
const content = fs.readFileSync('setup.js', 'utf8');
const requiredFunctions = [
  'setupRPCEndpoint',
  'setupPoolRegistry',
  'setupTokenEquivalence',
  'setupArbitrageABI',
  'setupPrivateKey',
  'setupMEVRelays',
  'setupMLModel',
  'setupMonitoring',
  'setupLogging',
  'setupAutomation',
  'writeEnvFile',
  'printSummary'
];

requiredFunctions.forEach(func => {
  test(
    `Function ${func} exists`,
    content.includes(`async function ${func}`) || content.includes(`function ${func}`)
  );
});

// Test 3: Check for example files
const exampleFiles = [
  '.env.example',
  'pool_registry.json.example',
  'token_equivalence.json.example',
  'MultiDEXArbitrageCore.abi.json.example'
];

exampleFiles.forEach(file => {
  test(`Example file ${file} exists`, fs.existsSync(file));
});

// Test 4: Check documentation
test('SETUP.md documentation exists', fs.existsSync('SETUP.md'));
test('README.md mentions setup script', fs.readFileSync('README.md', 'utf8').includes('yarn setup'));
test('QUICKSTART.md mentions setup script', fs.readFileSync('QUICKSTART.md', 'utf8').includes('yarn setup'));

// Test 5: Check package.json
const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
test('package.json has setup script', packageJson.scripts && packageJson.scripts.setup === 'node setup.js');

// Test 6: Check .gitignore
const gitignore = fs.readFileSync('.gitignore', 'utf8');
test('.gitignore excludes .env', gitignore.includes('.env'));
test('.gitignore allows .env.example', gitignore.includes('!.env.example'));
test('.gitignore excludes logs/', gitignore.includes('logs/'));

// Summary
console.log('\n' + '='.repeat(50));
console.log(`Tests passed: ${passed}`);
console.log(`Tests failed: ${failed}`);
console.log('='.repeat(50));

if (failed === 0) {
  console.log('\n✓ All setup tests passed!');
  process.exit(0);
} else {
  console.log(`\n✗ ${failed} test(s) failed`);
  process.exit(1);
}
