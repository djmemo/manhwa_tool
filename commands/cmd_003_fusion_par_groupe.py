"""
cmd_003_fusion_par_groupe.py — Fusion par groupes de N pages.
Qualité JPEG lue depuis .role.yaml > config.qscale_groupe (défaut 92).
"""
import os
import re
from PIL import Image
from session import session
from core.role_manager import read_role_yaml
from core.status_manager import mark_etape_done
from core.project_manager import list_chapters
from core.changelog import add_entry
from ui.colors import ok, warn, info, title
from ui.menu_engine import menu, pause, prompt_int, _clear
from ui.progress_bar import ProgressBar

LABEL = "🔗  Fusion par groupe de pages"
DESCRIPTION = "Fusionne 03_Clean_JPEG/ par groupes de N pages en fichiers segmentés"


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
    src_path = os.path.join(chapter_path, "03_Clean_JPEG")
    dst_path = os.path.join(chapter_path, "04_Final_Merged")

    images = _list_images_sorted(src_path)
    if not images:
        print(warn("  Aucune image dans 03_Clean_JPEG/"))
        pause()
        return

    # Lire la qualité JPEG depuis .role.yaml
    role_data = read_role_yaml(role_path) or {}
    quality = int(role_data.get("config", {}).get("qscale_groupe", 92))

    _clear()
    print(title(f"\n  🔗  Fusion par groupe — {chapter_name}\n"))
    print(info(f"  {len(images)} image(s) trouvée(s) | qualité JPEG : {quality}"))
    print()

    group_size = prompt_int("  Pages par groupe", default=10)
    if group_size <= 0:
        print(warn("  Taille invalide."))
        pause()
        return

    os.makedirs(dst_path, exist_ok=True)
    groups = _split_into_groups(images, group_size)
    print(info(f"\n  {len(groups)} groupe(s) de {group_size} page(s) max\n"))

    bar = ProgressBar(len(images), label="Fusion par groupe")
    total_processed = 0
    output_files = []

    for g_idx, group in enumerate(groups):
        loaded = []
        for img_name in group:
            img = Image.open(os.path.join(src_path, img_name)).convert("RGB")
            loaded.append(img)
            total_processed += 1
            bar.update(total_processed, suffix=img_name)

        total_h = sum(im.height for im in loaded)
        width = max(im.width for im in loaded)
        merged = Image.new("RGB", (width, total_h), (255, 255, 255))
        y = 0
        for im in loaded:
            merged.paste(im, (0, y))
            y += im.height

        out_name = f"group_{g_idx + 1:03d}.jpg"
        out_path = os.path.join(dst_path, out_name)
        merged.save(out_path, "JPEG", quality=quality)
        output_files.append(out_name)

    bar.done()

    mark_etape_done(chapter_path, "fusion_finale")
    project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
    add_entry(
        project_yaml, session.role_label,
        f"{chapter_name} — fusion par groupe ({len(groups)} fichier(s), {len(images)} pages, qualité {quality})"
    )

    print(ok(f"\n  ✔ {len(output_files)} fichier(s) créé(s) dans {dst_path} :"))
    for f in output_files:
        print(f"    • {f}")
    pause()


def _list_images_sorted(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    files = [f for f in os.listdir(path) if os.path.splitext(f.lower())[1] in exts]

    def sort_key(name: str):
        nums = re.findall(r"\d+", name)
        return [int(n) for n in nums] if nums else [0]

    return sorted(files, key=sort_key)


def _split_into_groups(items: list, size: int) -> list[list]:
    return [items[i: i + size] for i in range(0, len(items), size)]
