@echo off
REM ==================================================================================
REM  Quant Arbitrage System: Hyperspeed X100 Edition
REM  ONE-CLICK INSTALL AND RUN - Windows Edition
REM ==================================================================================

color 0A
echo.
echo ================================================================================
echo   $$$$$$\                                  $$\             $$$$$$\            $$\       
echo  $$  __$$\                                 $$ |           $$  __$$\           $$ |      
echo  $$ /  $$ |$$\   $$\  $$$$$$\  $$$$$$$\ $$$$$$\          $$ /  $$ | $$$$$$\  $$$$$$$\  
echo  $$ |  $$ |$$ |  $$ | \____$$\ $$  __$$\\_$$  _|         $$$$$$$$ |$$  __$$\ $$  __$$\ 
echo  $$ |  $$ |$$ |  $$ | $$$$$$$ |$$ |  $$ | $$ |           $$  __$$ |$$ |  \__|$$ |  $$ |
echo  $$ $$\$$ |$$ |  $$ |$$  __$$ |$$ |  $$ | $$ |$$\        $$ |  $$ |$$ |      $$ |  $$ |
echo  \$$$$$$ / \$$$$$$  |\$$$$$$$ |$$ |  $$ | \$$$$  |       $$ |  $$ |$$ |      $$$$$$$  |
echo   \___$$$\  \______/  \_______|\__|  \__|  \____/        \__|  \__|\__|      \_______/ 
echo       \___|                                                                             
echo.
echo   QUANT ARBITRAGE SYSTEM: HYPERSPEED X100 EDITION
echo   One-Click Install and Run - Windows Edition
echo ================================================================================
echo.

REM Check for Node.js
echo [STEP 1/6] Checking prerequisites...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed!
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo Recommended version: 18.x or higher
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js detected: 
node --version

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python is not installed or not in PATH.
    echo Python orchestration features will be limited.
    echo.
    echo To enable full functionality, install Python 3.8+ from: https://www.python.org/
) else (
    echo [OK] Python detected:
    python --version
)

echo.
echo [STEP 2/6] Installing backend dependencies...
cd backend
call npm install
if errorlevel 1 (
    echo [ERROR] Backend installation failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [STEP 3/6] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Frontend installation failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [STEP 4/6] Installing arbitrage engine dependencies...
cd ultra-fast-arbitrage-engine
call npm install
if errorlevel 1 (
    echo [ERROR] Arbitrage engine installation failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [STEP 5/6] Building arbitrage engine...
cd ultra-fast-arbitrage-engine
call npm run build
if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [STEP 6/6] Installing Python dependencies (if Python available)...
python -m pip --version >nul 2>&1
if not errorlevel 1 (
    python -m pip install -r requirements.txt >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Some Python dependencies failed to install
        echo System will run with limited Python functionality
    ) else (
        echo [OK] Python dependencies installed
    )
) else (
    echo [SKIPPED] Python not available
)

echo.
echo ================================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================================
echo.
echo Starting the system...
echo.

REM Start backend in new window
echo [LAUNCHING] Backend API on port 3001...
start "Quant Arbitrage Backend" cmd /k "cd backend && npm start"
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo [LAUNCHING] Frontend Dashboard on port 3000...
start "Quant Arbitrage Frontend" cmd /k "cd frontend && python -m http.server 3000 || npx http-server -p 3000"
timeout /t 2 /nobreak >nul

echo.
echo ================================================================================
echo   SYSTEM IS RUNNING!
echo ================================================================================
echo.
echo   Access URLs:
echo   ------------
echo   Dashboard:     http://localhost:3000
echo   Backend API:   http://localhost:3001
echo   API Health:    http://localhost:3001/api/health
echo.
echo   Windows opened:
echo   - Backend API server (port 3001)
echo   - Frontend Dashboard (port 3000)
echo.
echo   To stop the system:
echo   - Close the opened terminal windows
echo   - Or press Ctrl+C in each window
echo.
echo ================================================================================
echo.
echo Opening dashboard in your browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo Press any key to exit this window (services will continue running)...
pause >nul
