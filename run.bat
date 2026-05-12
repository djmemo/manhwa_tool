@echo off
:: ─────────────────────────────────────────────────────────────────
::  Manhwa Tool — Lanceur Windows
::  Installe uv si absent, synchronise les dépendances, lance l'outil.
::
::  Usage :
::    run.bat                    → mode interactif (défaut)
::    run.bat --watch            → surveillance 00_Raw/
::    run.bat --batch [projet]   → mode non-interactif
::    run.bat --config [fichier] → config.yaml alternatif
::    run.bat --dev              → installe aussi les dépendances de dev (pytest)
:: ─────────────────────────────────────────────────────────────────
setlocal enabledelayedexpansion
cd /d "%~dp0"

:: ── 1. Vérifier / installer uv ───────────────────────────────────────────────
where uv >nul 2>&1
if errorlevel 1 (
    echo [INFO] 'uv' non trouve. Installation en cours...

    :: Tentative via winget (Windows 10/11)
    where winget >nul 2>&1
    if not errorlevel 1 (
        winget install --id=astral-sh.uv -e --silent
        goto :check_uv_again
    )

    :: Tentative via pip
    where pip >nul 2>&1
    if not errorlevel 1 (
        pip install uv --quiet
        goto :check_uv_again
    )

    echo [ERREUR] Impossible d'installer 'uv' automatiquement.
    echo          Installez-le manuellement : https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

:check_uv_again
where uv >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Installation de 'uv' echouee. Redemarrez le terminal apres installation manuelle.
    pause
    exit /b 1
)

:: ── 2. Synchroniser les dépendances (crée/met à jour le venv si besoin) ──────
echo [INFO] Vérification des dépendances...

:: Détecter --dev dans les arguments
set "SYNC_EXTRAS="
for %%A in (%*) do (
    if "%%A"=="--dev" set "SYNC_EXTRAS=--extra dev"
)

uv sync %SYNC_EXTRAS% --quiet
if errorlevel 1 (
    echo [ERREUR] uv sync a échoue. Vérifiez pyproject.toml.
    pause
    exit /b 1
)

:: ── 3. Filtrer --dev des arguments transmis à main.py ────────────────────────
set "ARGS="
for %%A in (%*) do (
    if not "%%A"=="--dev" set "ARGS=!ARGS! %%A"
)

:: ── 4. Lancer l'application ───────────────────────────────────────────────────
uv run python main.py %ARGS%
