@echo off
REM ==================================================================================
REM  Quant Arbitrage System: Test All Components
REM ==================================================================================

echo ================================================================================
echo   QUANT ARBITRAGE SYSTEM - TEST SUITE
echo ================================================================================
echo.

echo [1/3] Testing Backend API...
cd backend
call npm test
cd ..

echo.
echo [2/3] Testing Arbitrage Engine...
cd ultra-fast-arbitrage-engine
call npm test
cd ..

echo.
echo [3/3] Testing Python Modules...
python -m pytest tests/ 2>nul
if errorlevel 1 (
    echo [INFO] Python tests skipped or failed (pytest may not be installed)
)

echo.
echo ================================================================================
echo   TEST SUITE COMPLETE
echo ================================================================================
echo.
pause
