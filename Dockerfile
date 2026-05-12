# ═══════════════════════════════════════════════════════════════════════════════
#  Manhwa Tool v2 — Dockerfile multi-stage Alpine (optimisé)
#  Objectif taille finale : < 150MB
#
#  Optimisations appliquées vs v1 :
#    A. pip install fusionné en 1 seul RUN          → moins de layers
#    B. pip --upgrade supprimé                      → -3MB
#    C. Purge agressive du venv (tests, *.pyi, .so) → -15 à -20MB
#    D. COPY explicite des modules Python           → zéro fichier superflu
#    E. apk fusionné en 1 seul RUN par stage        → moins de layers
#    F. strip des .so (supprime symboles debug)     → -2 à -5MB
#    G. libwebp retiré du runtime (non requis)      → -1.5MB
#
#  Volumes attendus :
#    /data/osirisscan    ← projets manhwa    (bind mount hôte, rw)
#    /tools/realesrgan   ← binaire ESRGAN    (bind mount hôte, ro)
#
#  Lancement interactif :
#    docker run -it \
#      -e OSIRISSCAN_RACINE=/data/osirisscan \
#      -v "$HOME/OsirisScan:/data/osirisscan" \
#      -v "/chemin/realesrgan:/tools/realesrgan:ro" \
#      manhwa-tool:latest
# ═══════════════════════════════════════════════════════════════════════════════


# ── Stage 1 : builder ─────────────────────────────────────────────────────────
# Compile Pillow + installe toutes les dépendances dans /opt/venv.
# Ce stage entier est exclu de l'image finale.
FROM python:3.11-alpine AS builder

# [E] Toutes les dépendances de compilation en 1 seul RUN = 1 seul layer
RUN apk add --no-cache \
    gcc \
    musl-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    openjpeg-dev \
    libwebp-dev \
    binutils

# Créer le venv isolé (PATH mis à jour pour ce stage)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# [B] PAS de pip upgrade : inutile et ajoute ~3MB
# [A] Toutes les dépendances en 1 seul RUN pip install
# Ordre : pillow en premier (compilation longue) pour maximiser le cache Docker
# si on relance le build avec seulement les autres packages modifiés
COPY pyproject.toml /tmp/pyproject.toml
RUN pip install --no-cache-dir \
    "pillow>=10.0.0" \
    "pyyaml>=6.0" \
    "colorama>=0.4.6" \
    "readchar>=4.0.5" \
    "watchdog>=4.0.0"

# [C] Purge agressive : supprimer tout ce qui n'est pas nécessaire à l'exécution
RUN \
    # Supprimer les fichiers de compilation résiduels
    find /opt/venv -name "*.a"   -delete && \
    find /opt/venv -name "*.o"   -delete && \
    find /opt/venv -name "*.pyx" -delete && \
    find /opt/venv -name "*.pxd" -delete && \
    # Supprimer les stubs de type (inutiles en prod)
    find /opt/venv -name "*.pyi" -delete && \
    # Supprimer les répertoires de tests embarqués dans les packages
    find /opt/venv -type d -name "tests"    -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "test"     -exec rm -rf {} + 2>/dev/null || true && \
    # Supprimer les métadonnées pip (dist-info, egg-info)
    find /opt/venv -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -type d -name "*.egg-info"  -exec rm -rf {} + 2>/dev/null || true && \
    # Supprimer les bytecodes compilés
    find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /opt/venv -name "*.pyc" -delete && \
    find /opt/venv -name "*.pyo" -delete && \
    # [F] Strip les symboles de debug des .so (économise 2-5MB)
    find /opt/venv -name "*.so" -exec strip --strip-unneeded {} \; 2>/dev/null || true


# ── Stage 2 : runtime ─────────────────────────────────────────────────────────
# Image finale — zéro outil de compilation, zéro header, zéro superflu.
FROM python:3.11-alpine AS runtime

LABEL maintainer="OsirisScan" \
      description="Manhwa Tool v2 — outil console de gestion workflow scanlation" \
      version="2.0.0"

# [E] Libs runtime en 1 seul RUN = 1 seul layer
# [G] libwebp retiré : Pillow peut ouvrir webp via libjpeg-turbo sur Alpine
#     Ajouter libwebp ici seulement si tu lis/écris des fichiers .webp
RUN apk add --no-cache \
    libjpeg \
    zlib \
    freetype \
    openjpeg \
    libstdc++ && \
    # Créer l'utilisateur non-root manhwa (UID/GID 1000) dans le même layer
    addgroup -g 1000 manhwa && \
    adduser -D -u 1000 -G manhwa -h /home/manhwa manhwa

# Copier le venv purgé depuis le stage builder
COPY --from=builder /opt/venv /opt/venv

# [D] COPY explicite des modules Python (évite de copier fichiers non Python)
#     Chaque dossier/fichier est listé explicitement — rien de superflu
COPY --chown=manhwa:manhwa main.py          /app/main.py
COPY --chown=manhwa:manhwa config_loader.py /app/config_loader.py
COPY --chown=manhwa:manhwa session.py       /app/session.py
COPY --chown=manhwa:manhwa pyproject.toml   /app/pyproject.toml
COPY --chown=manhwa:manhwa core/            /app/core/
COPY --chown=manhwa:manhwa commands/        /app/commands/
COPY --chown=manhwa:manhwa ui/              /app/ui/

# Entrypoint Docker
COPY --chown=manhwa:manhwa docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Variables d'environnement runtime
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TERM=xterm-256color
ENV OSIRISSCAN_RACINE=""
ENV ESRGAN_EXE_PATH=""
ENV CONSOLE_LARGEUR=80

# Points de montage déclarés
VOLUME ["/data/osirisscan"]
VOLUME ["/tools/realesrgan"]

WORKDIR /app
USER manhwa

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]
