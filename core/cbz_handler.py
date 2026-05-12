"""
core/cbz_handler.py — Extraction et gestion des archives .cbz/.zip.
Ne modifie jamais l'archive source (00_Raw/ en lecture seule).
"""
import os
import zipfile
from ui.progress_bar import ProgressBar

EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def list_cbz(raw_path: str) -> list[str]:
    if not os.path.isdir(raw_path):
        return []
    return sorted([f for f in os.listdir(raw_path) if f.lower().endswith((".cbz", ".zip"))])


def detect_duplicates(archive_name: str, dest_path: str) -> bool:
    if not os.path.isdir(dest_path):
        return False
    return any(_is_image(f) for f in os.listdir(dest_path))


def extract_cbz(cbz_path: str, dest_path: str, progress_callback=None) -> list[str]:
    """
    Extrait vers dest_path. Gère images à la racine ou dans un sous-dossier.
    Ne modifie jamais cbz_path.
    """
    os.makedirs(dest_path, exist_ok=True)
    extracted = []

    with zipfile.ZipFile(cbz_path, "r") as zf:
        members = zf.namelist()
        image_members = [m for m in members if _is_image(m)]
        if not image_members:
            return []

        total = len(image_members)
        bar = ProgressBar(total, label="Extraction") if progress_callback is None else None

        for i, member in enumerate(image_members):
            filename = os.path.basename(member)
            if not filename:
                continue
            dest_file = os.path.join(dest_path, filename)
            with zf.open(member) as src, open(dest_file, "wb") as dst:
                dst.write(src.read())
            extracted.append(dest_file)

            if bar:
                bar.update(i + 1, suffix=filename)
            elif progress_callback:
                progress_callback(i + 1, total, filename)

        if bar:
            bar.done(f"{total} image(s) extraite(s)")

    return extracted


def _is_image(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in EXTENSIONS_IMAGES
