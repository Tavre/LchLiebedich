@echo off
chcp 65001 >nul
echo Starting LchLiebeDich Bot System...
echo.

echo [1/2] Starting OneBot Engine...
start "OneBot Engine" /D "d:\lchliebedich\engine" cmd /c "set HTTP_PROXY= & set HTTPS_PROXY= & set ALL_PROXY= & Lagrange.OneBot.exe"

echo [2/2] Starting Bot Framework...
start "LchLiebedich" /D "d:\lchliebedich" cmd /c ".venv\Scripts\activate && python main.py"

echo.
pause >nul