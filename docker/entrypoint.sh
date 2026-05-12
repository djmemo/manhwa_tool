#!/bin/sh
# ═══════════════════════════════════════════════════════════════════════════════
#  entrypoint.sh — Manhwa Tool v2
#  POSIX sh (Alpine n'a pas bash par défaut)
#
#  Génère /tmp/manhwa_config.yaml depuis les variables d'environnement,
#  puis lance main.py en lui transmettant tous les arguments reçus ("$@").
#
#  Si --config est déjà dans les arguments, on ne génère PAS le config
#  temporaire et on laisse main.py utiliser celui fourni.
# ═══════════════════════════════════════════════════════════════════════════════
set -eu

# ── Vérifier si --config est déjà fourni dans les arguments ──────────────────
has_config_flag=0
for arg in "$@"; do
    if [ "$arg" = "--config" ]; then
        has_config_flag=1
        break
    fi
done

# ── Générer le config temporaire si --config absent ──────────────────────────
if [ "$has_config_flag" = "0" ]; then

    # Valeurs par défaut si les variables d'environnement sont vides
    RACINE="${OSIRISSCAN_RACINE:-/data/osirisscan}"
    ESRGAN="${ESRGAN_EXE_PATH:-/tools/realesrgan/realesrgan-ncnn-vulkan}"
    LARGEUR="${CONSOLE_LARGEUR:-80}"

    CONFIG_FILE="/tmp/manhwa_config.yaml"

    # Générer le fichier YAML de configuration
    cat > "$CONFIG_FILE" << EOF
machine:
  racine_osirisscan: "${RACINE}"

upscale:
  exe_path: "${ESRGAN}"

console:
  largeur_banniere: ${LARGEUR}
EOF

    # Lancer main.py avec le config généré
    exec python main.py --config "$CONFIG_FILE" "$@"
else
    # --config fourni : laisser main.py gérer lui-même
    exec python main.py "$@"
fi
