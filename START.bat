@echo off
title Deal Hunter
echo.
echo  ==========================================
echo   DEAL HUNTER - Chasseur de bonnes affaires
echo  ==========================================
echo.
echo [1/2] Installation des dependances...
pip install requests beautifulsoup4 html5lib thefuzz Pillow --quiet
echo  OK !
echo.
echo [2/2] Lancement...
python deal_hunter.py
pause
