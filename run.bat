@echo off
cd /d "%~dp0"
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] uv non trouve. Installez-le : https://docs.astral.sh/uv/
    pause
    exit /b 1
)
uv sync --no-install-project
if %errorlevel% neq 0 (
    echo [ERREUR] Echec de l installation des dependances.
    pause
    exit /b 1
)
uv run python main.py
pause
