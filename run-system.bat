@echo off
REM ==================================================================================
REM  Quant Arbitrage System: Run System (assumes dependencies already installed)
REM ==================================================================================

echo ================================================================================
echo   QUANT ARBITRAGE SYSTEM - STARTING SERVICES
echo ================================================================================
echo.

echo [LAUNCHING] Backend API on port 3001...
start "Quant Arbitrage Backend" cmd /k "cd backend && npm start"
timeout /t 3 /nobreak >nul

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
echo   To stop: Close the terminal windows or press Ctrl+C
echo.
echo ================================================================================
echo.
echo Opening dashboard in your browser...
timeout /t 2 /nobreak >nul
start http://localhost:3000

echo.
echo Press any key to exit this window (services will continue running)...
pause >nul
