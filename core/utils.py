import os
import sys
import yaml
import subprocess
from typing import Any

EXTS_IMAGE = (".jpg", ".jpeg", ".png", ".webp")

def lire_yaml(chemin_fichier: str, defaut: Any = None) -> Any:
    """Lit un fichier YAML en toute sécurité et retourne son contenu."""
    if not os.path.isfile(chemin_fichier):
        return defaut if defaut is not None else {}
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or (defaut if defaut is not None else {})
    except yaml.YAMLError:
        return defaut if defaut is not None else {}

def ecrire_yaml(chemin_fichier: str, data: Any) -> None:
    """Écrit des données dans un fichier YAML proprement formaté."""
    os.makedirs(os.path.dirname(chemin_fichier) or ".", exist_ok=True)
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

def ouvrir_explorateur(chemin: str) -> None:
    """Ouvre le dossier spécifié dans l'explorateur natif du système."""
    if not os.path.exists(chemin):
        return
    if sys.platform == "win32":
        os.startfile(chemin)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", chemin])
    else:
        subprocess.Popen(["xdg-open", chemin])

def lister_images(dossier: str, extensions: tuple[str, ...] = EXTS_IMAGE) -> list[str]:
    """Retourne la liste triée des chemins absolus des images d'un dossier."""
    if not os.path.exists(dossier):
        return []
    return sorted(
        os.path.join(dossier, f) for f in os.listdir(dossier)
        if f.lower().endswith(extensions)
    )

import threading

def run_in_worker(fn: callable) -> None:
    """Lance une fonction dans un thread daemon non bloquant."""
    t = threading.Thread(target=fn, daemon=True)
    t.start()

import re as _re

def normaliser_nom_chapitre(archive_name: str) -> str:
    """
    Normalise le nom d'un chapitre au format 'Chapter XXX' (3 chiffres min).
    Fonctionne avec n'importe quel format de nom d'archive CBZ.
    Ex: 'Chapter 68_b706fa.cbz' → 'Chapter 068'
        'ch10.cbz'              → 'Chapter 010'
        '001.cbz'               → 'Chapter 001'
    """
    sans_ext = os.path.splitext(archive_name)[0]
    match = _re.search(r'(\d+)', sans_ext)
    if match:
        return f"Chapter {int(match.group(1)):03d}"
    # Fallback : nom brut nettoyé du hash
    return _re.sub(r'_[0-9a-f]{6,8}$', '', sans_ext).strip()
