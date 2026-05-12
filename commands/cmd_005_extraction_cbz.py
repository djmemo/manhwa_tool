"""
cmd_005_extraction_cbz.py — Extraction d'archives CBZ vers 01_Original_RAW/.
"""
import os
from session import session
from core.cbz_handler import list_cbz, detect_duplicates, extract_cbz
from core.status_manager import mark_etape_done
from core.changelog import add_entry
from core.project_manager import list_chapters
from ui.colors import ok, err, warn, info
from ui.menu_engine import menu, pause, _clear

LABEL = "📦  Extraire un CBZ"
DESCRIPTION = "Extrait une archive CBZ de 00_Raw/ vers 01_Original_RAW/ du chapitre"


def run():
    _clear()
    raw_path = os.path.join(session.projet_chemin, "00_Raw")
    cbz_list = list_cbz(raw_path)

    if not cbz_list:
        print(warn("\n  Aucune archive CBZ dans 00_Raw/"))
        pause()
        return

    idx = menu("Choisir l'archive à extraire", cbz_list, breadcrumb=session.breadcrumb())
    if idx is None:
        return

    cbz_name = cbz_list[idx]
    cbz_path = os.path.join(raw_path, cbz_name)

    role_path = os.path.join(session.projet_chemin, session.role_dossier)
    chapters = list_chapters(role_path)
    if not chapters:
        print(warn("  Créez d'abord un chapitre (commande 001)."))
        pause()
        return

    ch_idx = menu("Vers quel chapitre extraire ?", chapters, breadcrumb=session.breadcrumb())
    if ch_idx is None:
        return

    chapter_name = chapters[ch_idx]
    chapter_path = os.path.join(role_path, chapter_name)
    dest_path = os.path.join(chapter_path, "01_Original_RAW")

    if detect_duplicates(cbz_name, dest_path):
        print(warn(f"\n  ⚠  Des images existent déjà dans 01_Original_RAW/"))
        print("  Écraser quand même ? [o/N] : ", end="", flush=True)
        if input().strip().lower() != "o":
            print(info("  Extraction annulée."))
            pause()
            return

    print(info(f"\n  Extraction de '{cbz_name}' → {chapter_name}/01_Original_RAW/\n"))
    extracted = extract_cbz(cbz_path, dest_path)

    if not extracted:
        print(warn("  Aucune image extraite (archive vide ou format non supporté)."))
        pause()
        return

    mark_etape_done(chapter_path, "extraction_cbz")
    project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
    add_entry(project_yaml, session.role_label,
              f"{chapter_name} — extraction CBZ '{cbz_name}' ({len(extracted)} images)")

    print(ok(f"\n  ✔ {len(extracted)} image(s) extraite(s) avec succès."))
    pause()
