#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  Manhwa Tool — Lanceur Linux / macOS
#  Installe uv si absent, synchronise les dépendances, lance l'outil.
#
#  Usage :
#    ./run.sh                    → mode interactif (défaut)
#    ./run.sh --watch            → surveillance 00_Raw/
#    ./run.sh --batch [projet]   → mode non-interactif
#    ./run.sh --config [fichier] → config.yaml alternatif
#    ./run.sh --dev              → installe aussi les dépendances de dev (pytest)
# ─────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

# ── Couleurs console ──────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERREUR]${NC} $*" >&2; }

# ── 1. Vérifier / installer uv ───────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    warn "'uv' non trouvé. Tentative d'installation automatique..."

    if curl -LsSf https://astral.sh/uv/install.sh | sh 2>/dev/null; then
        # Sourcer le PATH mis à jour par l'installeur uv
        export PATH="$HOME/.local/bin:$PATH"
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    if ! command -v uv &>/dev/null; then
        error "Installation de 'uv' échouée."
        error "Installez-le manuellement : https://docs.astral.sh/uv/getting-started/installation/"
        error "Puis relancez : ./run.sh"
        exit 1
    fi
    info "'uv' installé avec succès."
fi

# ── 2. Synchroniser les dépendances ──────────────────────────────────────────
info "Vérification des dépendances..."

# Détecter --dev dans les arguments
SYNC_EXTRAS=""
ARGS=()
for arg in "$@"; do
    if [[ "$arg" == "--dev" ]]; then
        SYNC_EXTRAS="--extra dev"
    else
        ARGS+=("$arg")
    fi
done

if ! uv sync $SYNC_EXTRAS --quiet; then
    error "uv sync a échoué. Vérifiez pyproject.toml."
    exit 1
fi

# ── 3. Lancer l'application ───────────────────────────────────────────────────
exec uv run python main.py "${ARGS[@]+"${ARGS[@]}"}"
