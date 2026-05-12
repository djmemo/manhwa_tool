@echo off
:: ─────────────────────────────────────────────────────────────────────────────
::  build.bat — Build l'image Docker manhwa-tool (Windows)
:: ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0"
set IMAGE=manhwa-tool:latest

echo.
echo   ══════════════════════════════════════════════
echo    Manhwa Tool v2 ^— Docker Build
echo   ══════════════════════════════════════════════
echo.

where docker >nul 2>&1
if errorlevel 1 (
    echo   [ERREUR] Docker non trouve.
    echo   Installez Docker Desktop : https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

echo   Debut du build (premiere fois : ~3-5 min)...
echo.

docker build --no-cache -t %IMAGE% .
if errorlevel 1 (
    echo   [ERREUR] Build echoue.
    pause
    exit /b 1
)

echo.
echo   ──────────────────────────────────────────────
for /f %%i in ('docker image inspect %IMAGE% --format={{.Size}}') do set SIZE=%%i
echo   Image buildee : %IMAGE%
echo   Taille brute  : %SIZE% bytes
echo.
echo   Lancement interactif :
echo.
echo   docker run -it ^
echo     -e OSIRISSCAN_RACINE=/data/osirisscan ^
echo     -v "%%USERPROFILE%%\OsirisScan:/data/osirisscan" ^
echo     -v "/chemin/realesrgan:/tools/realesrgan:ro" ^
echo     %IMAGE%
echo.
echo   Verifier l'utilisateur :
echo   docker run --rm %IMAGE% sh -c "whoami ^&^& id"
echo   ══════════════════════════════════════════════
pause
