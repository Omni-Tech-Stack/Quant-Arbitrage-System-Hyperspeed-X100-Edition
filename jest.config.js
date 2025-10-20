module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  collectCoverageFrom: [
    'ultra-fast-arbitrage-engine/index.ts',
    '!ultra-fast-arbitrage-engine/**/*.test.ts',
    '!**/node_modules/**',
    '!**/dist/**',
    '!**/native/**'
  ],
  coverageThreshold: {
    global: {
      statements: 63,
      branches: 63,
      functions: 63,
      lines: 63
    }
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  transform: {
    '^.+\\.ts$': 'ts-jest'
  },
  testTimeout: 10000,
  verbose: true
};
