@echo off
chcp 65001 >nul
echo Starting LchLiebeDich Bot System...
echo.

echo [1/2] Starting OneBot Engine...
start "OneBot Engine" /D "d:\lchliebedich\engine" cmd /c "set HTTP_PROXY= & set HTTPS_PROXY= & set ALL_PROXY= & Lagrange.OneBot.exe"

echo [2/2] Starting Bot Framework...
start "Bot Framework" /D "d:\lchliebedich" cmd /c "python main.py"

echo.
echo Both services are starting in separate windows.
echo Press any key to exit this launcher...
pause >nul