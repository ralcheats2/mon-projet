@echo off
title Deal Hunter - Chasseur de Bonnes Affaires
echo.
echo  ██████  ███████  █████  ██       
echo  ██   ██ ██      ██   ██ ██       
echo  ██   ██ █████   ███████ ██       
echo  ██   ██ ██      ██   ██ ██       
echo  ██████  ███████ ██   ██ ███████  
echo  HUNTER - Chasseur de bonnes affaires
echo.
echo [1/3] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe!
    echo Telecharge Python sur https://python.org
    pause
    exit
)
echo [2/3] Installation des dependances...
pip install -r requirements.txt --quiet
echo [3/3] Lancement de l'application...
echo.
echo  Ouvre ton navigateur sur: http://localhost:5000
echo  Appuie sur CTRL+C pour arreter
echo.
start http://localhost:5000
python app.py
pause
