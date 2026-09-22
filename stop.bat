@echo off
title BHUMI-FUSION Shutdown
echo ================================================================
echo           Stopping BHUMI-FUSION Services...
echo ================================================================
echo.

cd /d "%~dp0"

echo [1/3] Stopping processes running on Port 8000 (Backend)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped Backend PID:' $_ } catch {} }"

echo [2/3] Stopping processes running on Port 5173 (Frontend)...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { try { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue; Write-Host 'Stopped Frontend PID:' $_ } catch {} }"

echo [3/3] Terminating launcher terminal windows...
taskkill /FI "WINDOWTITLE eq BHUMI-FUSION Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BHUMI-FUSION Frontend*" /F >nul 2>&1

echo.
echo ================================================================
echo   All BHUMI-FUSION services have been stopped.
echo   Ports 8000 and 5173 are now free.
echo ================================================================
echo.
ping 127.0.0.1 -n 2 >nul
