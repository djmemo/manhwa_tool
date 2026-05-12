# Manhwa Tool v2

Outil console de gestion de workflow scanlation (cleaning, upscale, fusion).

---

## Installation

### Prérequis

| Outil | Requis | Installation |
|---|---|---|
| Python 3.11+ | ✔ | https://www.python.org/downloads/ |
| `uv` | ✔ (auto-installé) | https://docs.astral.sh/uv/ |
| Real-ESRGAN | Optionnel | https://github.com/xinntao/Real-ESRGAN |

> **`uv` est installé automatiquement** par `run.bat` / `run.sh` si absent.
> Si l'installation automatique échoue, installez-le manuellement :
> ```
> pip install uv
> ```

---

## Démarrage rapide

### Windows
```bat
run.bat
```

### Linux / macOS
```bash
chmod +x run.sh   # une seule fois
./run.sh
```

### Premier lancement
Au premier lancement, `racine_osirisscan` sera demandée si elle n'est pas configurée.
Ce chemin pointe vers le dossier parent de vos projets (ex : `D:\OsirisScan`).
Il est sauvegardé dans `config.yaml` pour les lancements suivants.

---

## Options

| Option | Description |
|---|---|
| *(aucune)* | Mode interactif (défaut) |
| `--dev` | Installe aussi les dépendances de développement (pytest) |
| `--watch` | Surveillance de `00_Raw/` en arrière-plan |
| `--batch` | Mode non-interactif pour automatisation |
| `--config <fichier>` | Chemin alternatif vers `config.yaml` |

---

## Configuration (`config.yaml`)

```yaml
machine:
  racine_osirisscan: "D:/OsirisScan"   # configuré au premier lancement

upscale:
  exe_path: "C:/Tools/realesrgan/realesrgan-ncnn-vulkan.exe"

console:
  largeur_banniere: 80
```

---

## Lancer les tests

```bash
./run.sh --dev          # installe pytest + dépendances dev
uv run pytest tests/    # exécute la suite complète
```

---

## Structure

```
manhwa_tool/
├── main.py               ← Point d'entrée
├── config.yaml           ← Configuration machine
├── config_loader.py      ← Chargement + save_racine()
├── session.py            ← Contexte runtime
├── run.bat / run.sh      ← Lanceurs (install auto de uv + uv sync)
├── pyproject.toml        ← Dépendances
├── core/                 ← Modules métier
├── commands/             ← Commandes auto-découvertes
├── ui/                   ← Interface console
└── tests/                ← Suite pytest (91 tests)
```

---

## Docker

### Build de l'image

```bash
docker build -t manhwa-tool:latest .
```

> Build sans cache (recommandé pour la prod) :
> ```bash
> docker build --no-cache -t manhwa-tool:latest .
> ```

### Lancement rapide (`docker run`)

```bash
docker run -it \
  -e OSIRISSCAN_RACINE=/data/osirisscan \
  -v "$HOME/OsirisScan:/data/osirisscan" \
  -v "/chemin/vers/realesrgan:/tools/realesrgan:ro" \
  manhwa-tool:latest
```

> ⚠️ **Toujours utiliser `-it`** (`--interactive --tty`).
> L'outil utilise `readchar` pour la navigation clavier — sans TTY la navigation est impossible.

### Lancement avec `docker compose`

```bash
# Copier et adapter le fichier d'environnement
cp docker/env.example .env
# Éditer OSIRISSCAN_HOST_PATH et ESRGAN_HOST_PATH dans .env

# Builder l'image
docker compose build

# Lancer une session interactive
docker compose run --rm manhwa-tool
```

### Variables d'environnement

| Variable | Défaut conteneur | Description |
|---|---|---|
| `OSIRISSCAN_RACINE` | `/data/osirisscan` | Chemin racine des projets dans le conteneur |
| `ESRGAN_EXE_PATH` | `/tools/realesrgan/realesrgan-ncnn-vulkan` | Binaire Real-ESRGAN |
| `CONSOLE_LARGEUR` | `80` | Largeur de la bannière console |
| `OSIRISSCAN_HOST_PATH` | `./data` | *(docker-compose)* Chemin hôte des projets |
| `ESRGAN_HOST_PATH` | *(vide)* | *(docker-compose)* Chemin hôte Real-ESRGAN |

### Volumes

| Volume conteneur | Mode | Usage |
|---|---|---|
| `/data/osirisscan` | `rw` | Projets manhwa (bind mount depuis l'hôte) |
| `/tools/realesrgan` | `ro` | Binaire Real-ESRGAN (bind mount depuis l'hôte) |

### Vérifier la taille de l'image

```bash
docker image inspect manhwa-tool:latest --format='{{.Size}}' | awk '{printf "%.1f MB\n", $1/1024/1024}'
# Objectif : < 150MB
```

### Vérifier l'utilisateur non-root

```bash
docker run --rm manhwa-tool:latest sh -c "whoami && id"
# → manhwa
# → uid=1000(manhwa) gid=1000(manhwa)
```
