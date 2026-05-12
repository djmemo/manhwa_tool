"""
cmd_001_creer_chapitre.py — Créer un nouveau chapitre.
"""
import os
import sys
import subprocess
from session import session
from core.project_manager import get_next_chapter_number
from core.role_manager import get_sous_dossiers
from core.status_manager import create_status
from core.changelog import add_entry
from ui.colors import ok, warn, info
from ui.menu_engine import prompt_int, pause, _clear

LABEL = "📁  Créer un chapitre"
DESCRIPTION = "Crée le dossier du prochain chapitre avec sous-dossiers et .status.yaml"


def run():
    _clear()
    role_path = os.path.join(session.projet_chemin, session.role_dossier)
    next_num = get_next_chapter_number(session.projet_chemin)

    print(info(f"\n  Prochain chapitre suggéré : {next_num}\n"))
    num = prompt_int("  Numéro de chapitre", default=next_num)
    chapter_name = f"Chapter {num:02d}"
    chapter_path = os.path.join(role_path, chapter_name)

    if os.path.isdir(chapter_path):
        print(warn(f"  Le dossier '{chapter_name}' existe déjà."))
        pause()
        return

    sous_dossiers = get_sous_dossiers(role_path)
    os.makedirs(chapter_path, exist_ok=True)
    for sd in sous_dossiers:
        os.makedirs(os.path.join(chapter_path, sd["nom"]), exist_ok=True)

    create_status(chapter_path, chapter_name, session.role_label)

    project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
    add_entry(project_yaml, session.role_label, f"{chapter_name} — dossier créé")

    # Ouvrir dans l'explorateur Windows
    if sys.platform == "win32":
        subprocess.Popen(["explorer", chapter_path])

    session.chapitre_actif = chapter_name
    print(ok(f"\n  ✔ '{chapter_name}' créé avec {len(sous_dossiers)} sous-dossiers."))
    print(info(f"     {chapter_path}"))
    pause()
