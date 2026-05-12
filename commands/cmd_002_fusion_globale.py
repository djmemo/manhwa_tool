"""
cmd_002_fusion_globale.py — Fusion globale de toutes les images JPEG.
Qualité JPEG lue depuis .role.yaml > config.qscale_global (défaut 95).
"""
import os
from PIL import Image
from session import session
from core.role_manager import read_role_yaml
from core.status_manager import mark_etape_done
from core.project_manager import list_chapters
from core.changelog import add_entry
from ui.colors import ok, warn, info, title
from ui.menu_engine import menu, pause, _clear
from ui.progress_bar import ProgressBar

LABEL = "🔗  Fusion globale JPEG"
DESCRIPTION = "Fusionne toutes les images de 04_Clean_JPEG/ en merged_output.jpg"


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
    src_path = os.path.join(chapter_path, "04_Clean_JPEG")
    dst_path = os.path.join(chapter_path, "05_Final_Merged")

    # Lire la qualité depuis .role.yaml
    role_data = read_role_yaml(role_path) or {}
    quality = int(role_data.get("config", {}).get("qscale_global", 95))

    images = _list_images_sorted(src_path)
    if not images:
        print(warn("  Aucune image dans 04_Clean_JPEG/"))
        pause()
        return

    os.makedirs(dst_path, exist_ok=True)
    _clear()
    print(title(f"\n  🔗  Fusion globale — {chapter_name}\n"))
    print(info(f"  {len(images)} image(s) | qualité JPEG : {quality}\n"))

    bar = ProgressBar(len(images), label="Chargement")
    loaded = []
    for i, img_name in enumerate(images):
        img = Image.open(os.path.join(src_path, img_name)).convert("RGB")
        loaded.append(img)
        bar.update(i + 1, suffix=img_name)
    bar.done("Chargement terminé")

    total_height = sum(im.height for im in loaded)
    width = max(im.width for im in loaded)
    merged = Image.new("RGB", (width, total_height), (255, 255, 255))

    y = 0
    for im in loaded:
        merged.paste(im, (0, y))
        y += im.height

    out_path = os.path.join(dst_path, "merged_output.jpg")
    merged.save(out_path, "JPEG", quality=quality)

    mark_etape_done(chapter_path, "fusion_finale")
    project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
    add_entry(
        project_yaml, session.role_label,
        f"{chapter_name} — fusion globale ({len(images)} pages, qualité {quality})"
    )

    print(ok(f"\n  ✔ Fusion terminée → {out_path}"))
    pause()


def _list_images_sorted(path: str) -> list[str]:
    import re
    if not os.path.isdir(path):
        return []
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    files = [f for f in os.listdir(path) if os.path.splitext(f.lower())[1] in exts]

    def sort_key(name: str):
        nums = re.findall(r"\d+", name)
        return [int(n) for n in nums] if nums else [0]

    return sorted(files, key=sort_key)
