@echo off
REM ==================================================================================
REM  Quant Arbitrage System: Install Dependencies Only
REM ==================================================================================

echo ================================================================================
echo   QUANT ARBITRAGE SYSTEM - DEPENDENCY INSTALLER
echo ================================================================================
echo.

echo [1/4] Installing backend dependencies...
cd backend
call npm install
if errorlevel 1 (
    echo [ERROR] Backend installation failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [2/4] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo [ERROR] Frontend installation failed!
    pause
    exit /b 1
)
cd ..

echo.
echo [3/4] Installing arbitrage engine dependencies...
cd ultra-fast-arbitrage-engine
call npm install
if errorlevel 1 (
    echo [ERROR] Arbitrage engine installation failed!
    pause
    exit /b 1
)
call npm run build
cd ..

echo.
echo [4/4] Installing Python dependencies...
python -m pip --version >nul 2>&1
if not errorlevel 1 (
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [WARNING] Some Python dependencies failed to install
    )
) else (
    echo [SKIPPED] Python not available
)

echo.
echo ================================================================================
echo   INSTALLATION COMPLETE!
echo ================================================================================
echo.
echo To start the system, run: run-system.bat
echo.
pause
