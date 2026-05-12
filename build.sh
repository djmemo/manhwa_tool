#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  build.sh — Build l'image Docker manhwa-tool et affiche la taille finale
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")"

IMAGE="manhwa-tool:latest"

echo ""
echo "  ══════════════════════════════════════════════"
echo "   Manhwa Tool v2 — Docker Build"
echo "  ══════════════════════════════════════════════"
echo ""

# Vérifier Docker
if ! command -v docker &>/dev/null; then
    echo "  [ERREUR] Docker non trouvé."
    echo "  Installez Docker Desktop : https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "  ▶  Build en cours... (première fois : ~3-5 min)"
echo ""

time docker build --no-cache -t "$IMAGE" . 2>&1

echo ""
echo "  ──────────────────────────────────────────────"

# Taille de l'image
SIZE=$(docker image inspect "$IMAGE" --format='{{.Size}}' 2>/dev/null)
SIZE_MB=$(echo "$SIZE" | awk '{printf "%.1f", $1/1024/1024}')
echo "  ✔  Image buildée : $IMAGE"
echo "  📦  Taille       : ${SIZE_MB} MB"

if (( $(echo "$SIZE_MB < 150" | bc -l) )); then
    echo "  ✅  Objectif < 150MB respecté !"
else
    echo "  ⚠️  Objectif < 150MB dépassé — analyser les layers :"
    echo "       docker history $IMAGE"
fi

echo ""
echo "  ──────────────────────────────────────────────"
echo "  Lancement interactif :"
echo ""
echo "  docker run -it \\"
echo "    -e OSIRISSCAN_RACINE=/data/osirisscan \\"
echo "    -v \"\$HOME/OsirisScan:/data/osirisscan\" \\"
echo "    -v \"/chemin/realesrgan:/tools/realesrgan:ro\" \\"
echo "    $IMAGE"
echo ""
echo "  Vérifier l'utilisateur non-root :"
echo "  docker run --rm $IMAGE sh -c \"whoami && id\""
echo "  ══════════════════════════════════════════════"
