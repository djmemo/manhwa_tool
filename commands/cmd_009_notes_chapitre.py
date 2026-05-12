"""
cmd_009_notes_chapitre.py — Lecture et ajout de notes sur un chapitre.
"""
import os
from session import session
from core.status_manager import read_status, add_note
from core.project_manager import list_chapters
from ui.colors import title, info, ok, warn, separator
from ui.menu_engine import menu, prompt_text, pause, _clear

LABEL = "📝  Notes de chapitre"
DESCRIPTION = "Lire et ajouter des notes libres sur un chapitre"


def run():
    _clear()
    role_path = os.path.join(session.projet_chemin, session.role_dossier)
    chapters = list_chapters(role_path)

    if not chapters:
        print(warn("  Aucun chapitre disponible."))
        pause()
        return

    idx = menu("Choisir le chapitre", chapters, breadcrumb=session.breadcrumb())
    if idx is None:
        return

    chapter_name = chapters[idx]
    chapter_path = os.path.join(role_path, chapter_name)

    while True:
        _clear()
        status = read_status(chapter_path)
        notes = status.get("notes", []) if status else []

        print(title(f"\n  📝  Notes — {chapter_name}\n"))
        print(separator(60))

        if not notes:
            print(info("  Aucune note pour ce chapitre."))
        else:
            for n in notes:
                date = n.get("date", "")
                texte = n.get("texte", "")
                print(f"  [{date}]  {texte}")

        print(separator(60))
        print(info(f"\n  {len(notes)} note(s)\n"))

        items = ["➕  Ajouter une note", "⬅  Retour"]
        choice = menu("", items, breadcrumb=session.breadcrumb())

        if choice is None or choice == 1:
            return

        if choice == 0:
            texte = prompt_text("  Texte de la note")
            if texte.strip():
                add_note(chapter_path, texte.strip())
                print(ok("  ✔ Note ajoutée."))
                pause()
            else:
                print(warn("  Note vide, ignorée."))
                pause()
