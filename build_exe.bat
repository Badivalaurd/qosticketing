@echo off
REM ============================================================
REM  QoS Ticketing — Script de compilation Windows
REM  Prérequis : pip install pyinstaller dans le venv actif
REM ============================================================

echo [1/4] Collecte des fichiers statiques...
python manage.py collectstatic --noinput --settings=config.settings_desktop
if errorlevel 1 (
    echo ERREUR : collectstatic a echoue.
    pause
    exit /b 1
)

echo [2/4] Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist

echo [3/4] Compilation avec PyInstaller...
pyinstaller launcher.spec --clean
if errorlevel 1 (
    echo ERREUR : PyInstaller a echoue.
    pause
    exit /b 1
)

echo [4/4] Copie du fichier de configuration reseau...
if not exist dist\QoSTicketing\data mkdir dist\QoSTicketing\data
copy /y network.env.example dist\QoSTicketing\data\network.env

echo.
echo ============================================================
echo  BUILD TERMINE
echo  Executable : dist\QoSTicketing.exe
echo  Taille     :
for %%F in (dist\QoSTicketing.exe) do echo              %%~zF octets
echo.
echo  Partager dist\QoSTicketing.exe sur SharePoint.
echo ============================================================
pause
