@echo off
title Deal Hunter - Chasseur de Bonnes Affaires
echo.
echo  ==========================================
echo   DEAL HUNTER - Chasseur de bonnes affaires
echo  ==========================================
echo.

echo [1/3] Verification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERREUR: Python n'est pas installe ou pas dans le PATH !
    echo  Telecharge Python sur https://python.org
    echo  IMPORTANT: Coche bien "Add Python to PATH" lors de l'installation.
    pause
    exit
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python detecte : %PYVER%
echo.

echo [2/3] Installation des dependances (pure Python, aucun compilateur requis)...
pip install --upgrade pip --quiet
pip install flask requests beautifulsoup4 html5lib fake-useragent apscheduler thefuzz flask-cors --quiet
if errorlevel 1 (
    echo.
    echo  ERREUR lors de l'installation. Essai avec pip3...
    pip3 install flask requests beautifulsoup4 html5lib fake-useragent apscheduler thefuzz flask-cors --quiet
)
echo  Dependances OK !
echo.

echo [3/3] Lancement de l'application...
echo.
echo  ==========================================
echo   Ouvre ton navigateur sur: http://localhost:5000
echo   Appuie sur CTRL+C pour arreter
echo  ==========================================
echo.
timeout /t 2 /nobreak >nul
start http://localhost:5000
python app.py
pause
