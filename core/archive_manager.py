"""
core/archive_manager.py — Archivage d'un chapitre terminé dans un ZIP.
Demande confirmation rouge avant toute action irréversible.
"""
import os
import zipfile
from datetime import datetime
from core.status_manager import read_status, mark_archive
from ui.colors import confirm_danger, ok, err


def est_archivable(chapter_path: str) -> bool:
    status = read_status(chapter_path)
    if status is None:
        return False
    return status.get("statut_global") == "termine"


def archive_chapter(chapter_path: str, archive_dest: str | None = None) -> str | None:
    if not est_archivable(chapter_path):
        print(err("Le chapitre n'est pas dans l'état 'terminé'. Archivage impossible."))
        return None

    chapter_name = os.path.basename(chapter_path)
    if archive_dest is None:
        archive_dest = os.path.dirname(chapter_path)

    date_str = datetime.now().strftime("%Y%m%d")
    zip_name = f"{chapter_name}_{date_str}.zip"
    zip_path = os.path.join(archive_dest, zip_name)

    if not confirm_danger(
        f"Archiver '{chapter_name}' → '{zip_name}' ?\n"
        "Cette action est irréversible et marque le chapitre comme archivé."
    ):
        return None

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(chapter_path):
            for file in files:
                if file.endswith(".yaml"):
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, chapter_path)
                zf.write(filepath, arcname)

    mark_archive(chapter_path)
    print(ok(f"Archive créée : {zip_path}"))
    return zip_path
