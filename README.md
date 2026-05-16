<div align="center">

# 🎌 Manhwa Tool v3

**TUI Textual — Workflow de scanlation/manhwa piloté par YAML**

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![Textual](https://img.shields.io/badge/Textual-TUI-blueviolet?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square)

</div>

---

## 📖 Présentation

**Manhwa Tool v3** est un outil de gestion de workflow de scanlation/manhwa en interface TUI
(Terminal User Interface) basé sur [Textual](https://textual.textualize.io/).
Il orchestre toute la vie d'un chapitre — depuis l'archive brute `.cbz` jusqu'au statut final
archivé — **sans base de données** : tout l'état est stocké dans des fichiers YAML sur disque.

### ✨ Fonctionnalités clés

- 📦 **Extraction automatique** des archives CBZ/ZIP vers l'espace de travail
- 🤖 **Upscale IA** via Real-ESRGAN (`01_Original_RAW` → `02_Upscale_RAW`)
- 👁 **Watchdog** — détection et traitement automatique des nouveaux CBZ déposés
- 🧩 **Recomposition** — fusion des pages découpées (`001__001.jpg` + `001__002.jpg` → `001.png`)
- 🖼 **Fusion globale** — toutes les images empilées en un seul PNG sans limite de hauteur
- 📊 **Suivi multi-rôles** — tableau d'avancement par rôle (Nettoyage, Traduction, Check…)
- 📝 **Changelog append-only** — historique complet de toutes les actions
- 🗜 **Export CBZ de release** — slicer webtoon avec découpe intelligente aux gouttières
- 🔁 **Pipeline complet** — orchestre toutes les étapes en un seul lancement

---

## 🗂 Structure de l'espace de travail

```
D:/OsirisScan/                          ← racine définie dans config.yaml
└── MonProjet/                          ← une œuvre
    ├── .project.yaml                   ← profil global, stats, changelog
    ├── 00_Raw/                         ← archives brutes (LECTURE SEULE)
    │   ├── Chapter001.cbz
    │   └── Chapter002.cbz
    ├── 01_Clean/                       ← rôle Nettoyage
    │   ├── .role.yaml                  ← config du rôle (modèle ESRGAN, qualité…)
    │   └── Chapter 001/
    │       ├── .status.yaml            ← suivi granulaire des étapes
    │       ├── 01_Original_RAW/        ← images extraites du CBZ
    │       ├── 02_Upscale_RAW/         ← images upscalées Real-ESRGAN
    │       ├── 02_Clean_PSD/           ← cleaning Photoshop (étape manuelle)
    │       ├── 03_Clean_JPEG/          ← exports JPEG du cleaning
    │       └── 04_Final_Merged/        ← fusion finale / release
    ├── 02_Trad/                        ← rôle Traduction
    └── 03_Check/                       ← rôle Check
```

---

## ⚙️ Installation

### Prérequis

| Outil | Version | Usage |
|---|---|---|
| [Python](https://www.python.org/) | 3.12+ | Runtime |
| [uv](https://docs.astral.sh/uv/) | latest | Gestionnaire de paquets |
| [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN/releases) | latest | Upscale IA (optionnel) |

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/djmemo/manhwa_tool.git
cd manhwa_tool

# 2. Installer les dépendances
uv sync

# 3. Lancer
uv run python main.py   # Linux / macOS
run.bat                  # Windows
```

> 💡 Au premier lancement, un écran de configuration demande le dossier racine ScanTrad.
> Ce chemin est ensuite sauvegardé dans `config.yaml`.

### `config.yaml`

```yaml
machine:
  racine_osirisscan: D:/ScanTrad

upscale:
  exe_path: C:/Tools/realesrgan/realesrgan-ncnn-vulkan.exe
```

---

## 🚀 Utilisation

### Flux de travail standard

#### Navigation à l'ouverture

```

SelectProjectScreen
→ SelectRoleScreen
├── [rôle 01_Clean + CBZ détectés] → CbzAlertScreen
│       ├── Cocher les archives à extraire (ou "Tout cocher")
│       ├── "Extraire" → extraction en séquence → MainMenuScreen
│       │   (chapitre actif = premier extrait, persisté dans .role.yaml)
│       └── "Ignorer" → MainMenuScreen
└── [autre rôle ou aucun CBZ en attente] → MainMenuScreen
(chapitre actif restauré depuis .role.yaml → dernier_chapitre_actif)

```

#### Pipeline de production

```

┌──────────────────────────────────────────────────────────────┐
│  1. Déposer le(s) CBZ dans 00_Raw/                           │
│                                                              │
│  2. Sélectionner le projet → rôle 01_Clean                   │
│     ↳ CbzAlertScreen détecte les CBZ non encore extraits     │
│       Cocher + Extraire → 01_Original_RAW/ (auto)            │
│                                                              │
│  3. cmd_004  Upscale Real-ESRGAN → 02_Upscale_RAW/           │
│                                                              │
│  4. [Manuel] Nettoyage Photoshop → 02_Clean_PSD/             │
│              Export JPEG → 03_Clean_JPEG/                    │
│                                                              │
│  5. cmd_002  Fusion globale → 04_Final_Merged/               │
│     cmd_003  Recomposition pages découpées → 04_Final_Merged │
│     cmd_011  Slicer webtoon + CBZ release                    │
└──────────────────────────────────────────────────────────────┘

```

### Watchdog automatique

Lancez `cmd_010` pour surveiller `00_Raw/` en tâche de fond.
Chaque nouveau CBZ déposé déclenche automatiquement l'extraction et l'upscale.
Relancez `cmd_010` pour arrêter le watcher.

### Pages découpées (recomposition)

Si vos images ont été découpées en parties avec la convention `__` :

```
03_Clean_JPEG/
  001__001.jpg   ┐
  001__002.jpg   ├─→ cmd_003 → 04_Final_Merged/001.png
  001__003.jpg   ┘
  002__001.jpg   ┐
  002__002.jpg   ├─→ cmd_003 → 04_Final_Merged/002.png
  003.jpg        ──→ cmd_003 → 04_Final_Merged/003.png  (copiée telle quelle)
```

---

## 📋 Commandes disponibles

| Commande | Label | Description |
|---|---|---|
| `cmd_000_selectionner_chapitre` | Sélectionner un chapitre | Reprend ou commence un chapitre existant dans le rôle actif |
| `cmd_001_creer_chapitre` | Créer un chapitre | Initialise un nouveau chapitre et son arborescence |
| `cmd_002_fusion_globale` | Fusion globale | Fusionne toutes les images de 03_Clean_JPEG en un seul PNG sans limite de hauteur |
| `cmd_003_fusion_par_groupe` | Recomposition pages découpées | Fusionne les parties __001/__002/... en pages complètes dans 04_Final_Merged |
| `cmd_004_upscale_realesrgan` | Upscale Real-ESRGAN | Améliore la résolution des images RAW via Real-ESRGAN (01_Original_RAW → 02_Upscale_RAW) |
| `cmd_005_extraction_cbz` | Extraction CBZ | Extrait une archive CBZ/ZIP vers 01_Original_RAW du chapitre actif |
| `cmd_006_pipeline_complet` | Pipeline Complet | Exécute le workflow entier du chapitre actif étape par étape |
| `cmd_007_avancement` | Avancement | Affiche la progression multi-rôles et exporte un rapport Markdown |
| `cmd_008_parametres` | Paramètres | Configuration du rôle actif (modèle, qualité, membres) et changelog |
| `cmd_009_notes_chapitre` | Notes Chapitre | Consulter et ajouter des notes sur les chapitres du rôle actif |
| `cmd_010_surveiller_raw` | Surveiller RAW | Démarre/Arrête le Watchdog — Auto-Extraction + Auto-Upscale à chaque nouveau CBZ |
| `cmd_011_export_intelligent` | Export Intelligent (Slicer) | Découpe les images fusionnées en tranches webtoon et génère un CBZ de release |

---

## 🏗 Architecture

```
manhwa_tool/
├── main.py                     ← Point d'entrée (Textual + mode batch)
├── config_loader.py            ← Singleton CFG (config.yaml)
├── session.py                  ← Contexte runtime SESSION (singleton)
├── config.yaml                 ← Configuration machine locale
│
├── core/                       ← Logique métier pure (sans dépendance UI)
│   ├── project_manager.py      ← Gestion projets (.project.yaml)
│   ├── role_manager.py         ← Gestion rôles (.role.yaml)
│   ├── status_manager.py       ← Suivi étapes (.status.yaml)
│   ├── cbz_handler.py          ← Extraction archives CBZ/ZIP
│   ├── integrity_checker.py    ← Vérification RAW vs Upscale
│   ├── changelog.py            ← Historique append-only
│   ├── archive_manager.py      ← Archivage ZIP final
│   ├── watcher.py              ← Watchdog 00_Raw (watchdog lib)
│   ├── slicer.py               ← Découpe intelligente webtoon
│   └── exporter.py             ← Export multi-format (PNG/JPEG/CBZ)
│
├── ui/                         ← Interface Textual (sans logique métier)
│   ├── app.py                  ← Classe ManhwaApp
│   ├── app_css.py              ← Styles CSS Textual
│   ├── notify.py               ← Notifications centralisées
│   ├── modals.py               ← ConfirmModal / DangerModal
│   ├── screens/                ← Écrans de l'application
│   │   ├── screen_select_project.py
│   │   ├── screen_select_role.py
│   │   ├── screen_main_menu.py
│   │   ├── screen_progression.py
│   │   └── ...
│   └── widgets/
│       ├── breadcrumb.py       ← Fil d'Ariane (OsirisScan > Projet > Rôle > Chapitre)
│       ├── progressbar.py
│       └── status_table.py
│
├── commands/                   ← Commandes auto-découvertes (cmd_NNN_*.py)
│   └── cmd_000 … cmd_011
│
└── tests/                      ← Suite pytest
    ├── conftest.py
    ├── test_commands.py
    ├── test_cmd003_recomposition.py
    └── ...
```

### Principes de conception

| Contrainte | Règle appliquée |
|---|---|
| Pas de base de données | Tout l'état est en fichiers YAML |
| `00_Raw` en lecture seule | Jamais d'écriture directe dans les archives brutes |
| Rôles tiers protégés | Écriture autorisée uniquement sur le rôle actif (`SESSION.role_dossier`) |
| Changelog immuable | Append-only, jamais de suppression ni réécriture |
| Architecture en couches | `core` pur → `commands` orchestrent → `ui` affiche |
| Actions destructrices | Toujours protégées par `DangerModal` |
| Chemins sûrs | `os.path.join()` obligatoire, concaténation interdite |

---

## 🧪 Tests

```bash
# Tous les tests
uv run pytest tests/ -v

# Un module spécifique
uv run pytest tests/test_cmd003_recomposition.py -v

# Avec couverture
uv run pytest tests/ --cov=core --cov-report=term-missing
```

---

## 📦 Dépendances

| Paquet | Version | Usage |
|---|---|---|
| [`textual`](https://github.com/Textualize/textual) | ≥ 0.60.0 | Interface TUI |
| [`Pillow`](https://python-pillow.org/) | ≥ 10.0.0 | Traitement d'images |
| [`pyyaml`](https://pyyaml.org/) | ≥ 6.0 | Fichiers YAML |
| [`watchdog`](https://github.com/gorakhargosh/watchdog) | ≥ 4.0.0 | Surveillance `00_Raw` |

---

## 🤝 Contribution

1. Fork le dépôt
2. Créer une branche : `git checkout -b feature/ma-fonctionnalite`
3. Respecter les conventions : `cmd_NNN_slug.py`, `core` sans dépendance UI
4. Ajouter les tests dans `tests/`
5. Ouvrir une Pull Request

---

## 📄 Licence

MIT — voir [LICENSE](LICENSE)

---

<div align="center">
<sub>Construit avec ❤️ pour la communauté scanlation francophone</sub>
</div>
