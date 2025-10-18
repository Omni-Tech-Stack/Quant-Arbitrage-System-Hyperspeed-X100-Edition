# Test Infrastructure Improvements

This document describes the improvements made to the test infrastructure to ensure robust and reliable test execution, especially in CI environments.

## Summary of Improvements

All test files have been updated to follow best practices for spawning and managing server processes during testing. The improvements address the following checklist items:

### ✅ Checklist Implementation

1. **spawn import verification** - All test files that spawn processes properly import `spawn` from `child_process`
2. **server.js path resolution** - Uses `path.join(__dirname, '..')` instead of string concatenation for cross-platform compatibility
3. **Server readiness detection** - Implements port probing and health check verification before running tests
4. **Process cleanup** - Properly kills serverProcess with SIGTERM/SIGKILL to avoid stray processes on CI
5. **Windows compatibility** - Uses `process.execPath` which works correctly on all platforms including Windows
6. **Cross-platform paths** - Uses `path.join()` instead of string concatenation throughout
7. **CI visibility** - Improved stdio handling to show server logs in CI environments

## File Changes

### 1. `web3-integration.test.js`

**Key Improvements:**
- Added `net` module for port probing
- Implemented `checkPort()` function to verify port availability
- Implemented `waitForServer()` function with health check validation
- Updated `startServer()` to use:
  - `process.execPath` instead of hardcoded 'node'
  - `path.join(__dirname, '..')` for cross-platform path handling
  - Explicit stdio configuration `['ignore', 'pipe', 'pipe']` for better control
  - Port probing + health check to ensure server is truly ready
  - Visible server output in CI via `process.env.CI` check
- Updated `stopServer()` to:
  - Use SIGTERM for graceful shutdown
  - Fallback to SIGKILL after 2 seconds if needed
  - Prevent stray processes on CI
- Added signal handlers for SIGINT and SIGTERM to ensure cleanup on test interruption

**Code Example:**
```javascript
// Port probe function
function checkPort(port, host = 'localhost') {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(1000);
    socket.once('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.once('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.once('error', () => {
      socket.destroy();
      resolve(false);
    });
    socket.connect(port, host);
  });
}

// Wait for server with port probing + health check
async function waitForServer(maxAttempts = 30, delayMs = 500) {
  for (let i = 0; i < maxAttempts; i++) {
    const isOpen = await checkPort(PORT);
    if (isOpen) {
      try {
        const response = await axios.get(`${API_BASE}/api/health`, { timeout: 2000 });
        if (response.data.status === 'ok') {
          return true;
        }
      } catch (error) {
        // Continue waiting
      }
    }
    if (i < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, delayMs));
    }
  }
  return false;
}

// Start server with proper error handling
serverProcess = spawn(process.execPath, ['server.js'], {
  cwd: path.join(__dirname, '..'),
  stdio: ['ignore', 'pipe', 'pipe']
});
```

### 2. `run-all-tests.js`

**Key Improvements:**
- Updated spawn call to use `process.execPath` instead of 'node'
- Changed stdio from 'pipe' to `['ignore', 'pipe', 'pipe']` for explicit control
- Enhanced server output visibility in CI:
  - Shows server stdout when `process.env.CI` is set
  - Shows server stdout when `process.env.VERBOSE` is set
  - Always shows stderr for error visibility
- Improved `stopServer()` with SIGTERM/SIGKILL fallback

**Code Example:**
```javascript
serverProcess = spawn(process.execPath, ['server.js'], {
  cwd: path.join(__dirname, '..'),
  stdio: ['ignore', 'pipe', 'pipe'],
  env: { ...process.env, DEMO_MODE: 'false' }
});

serverProcess.stdout.on('data', (data) => {
  // Show server output in CI or verbose mode for debugging
  if (process.env.VERBOSE || process.env.CI) {
    console.log(`[Server] ${data.toString().trim()}`);
  }
});

serverProcess.stderr.on('data', (data) => {
  // Always show errors
  console.error(`[Server Error] ${data.toString().trim()}`);
});
```

### 3. `unit/api.test.js` and `feature/arbitrage-scenarios.test.js`

**Status:**
- These files don't spawn their own server processes
- They rely on `run-all-tests.js` to manage the server lifecycle
- No changes needed for these files

## Benefits

1. **Reliability**: Port probing + health checks ensure tests don't start until server is truly ready
2. **CI Compatibility**: Proper process cleanup prevents stray processes on CI
3. **Cross-Platform**: Works correctly on Windows, Linux, and macOS
4. **Debuggability**: Server logs visible in CI when needed
5. **Robustness**: Graceful shutdown with SIGTERM/SIGKILL fallback
6. **Race Condition Prevention**: No more test failures due to server not being ready

## Running Tests

### Run all tests (recommended)
```bash
cd backend
npm test
```

### Run unit tests only
```bash
cd backend
npm run test:unit
```

### Run feature/scenario tests only
```bash
cd backend
npm run test:feature
```

### Run web3 integration tests
```bash
cd backend/tests
node web3-integration.test.js
```

### Enable verbose mode
```bash
VERBOSE=1 npm test
```

### CI mode (auto-detected)
```bash
CI=1 npm test
```

## Troubleshooting

### Tests hang or timeout
- Check if port 3001 is already in use: `lsof -i :3001` (Unix) or `netstat -ano | findstr :3001` (Windows)
- Kill any existing node processes using that port
- Increase timeout if needed in test configuration

### Server won't start
- Check server.js exists in backend directory
- Verify all dependencies are installed: `npm install`
- Check for syntax errors: `node backend/server.js`

### Stray processes on CI
- The improved cleanup with SIGTERM/SIGKILL should prevent this
- If issues persist, check CI logs for error messages
- Verify signal handlers are being called

## Environment Variables

- `API_BASE_URL`: Override default API URL (default: http://localhost:3001)
- `PORT`: Override server port (default: 3001)
- `VERBOSE`: Enable verbose logging
- `CI`: Enable CI mode (auto-shows server logs)
- `DEMO_MODE`: Set to 'false' to disable demo data simulation during tests

## Future Improvements

Potential areas for future enhancement:

1. Add test coverage reporting
2. Implement parallel test execution where possible
3. Add performance benchmarking
4. Mock external RPC calls to avoid network dependency
5. Add integration with test databases for stateful tests
6. Implement test fixtures and factories for test data
