"""
cmd_004_upscale_realesrgan.py — Upscale via Real-ESRGAN-ncnn-vulkan.
"""
import os
import time
import subprocess
from session import session
from config_loader import CFG
from core.role_manager import read_role_yaml
from core.status_manager import mark_etape_done, update_integrite
from core.integrity_checker import check_integrity, list_images
from core.changelog import add_entry
from core.project_manager import list_chapters
from ui.colors import ok, err, warn, info
from ui.menu_engine import menu, pause, _clear
from ui.progress_bar import ProgressBar, fmt_duration

LABEL = "⚡  Upscale Real-ESRGAN"
DESCRIPTION = "Lance l'upscale des images RAW via Real-ESRGAN-ncnn-vulkan"


def run():
    _clear()
    exe = CFG.upscale.exe_path or ""
    if not os.path.isfile(exe):
        print(err(f"\n  Real-ESRGAN introuvable : {exe}"))
        print(warn("  Vérifiez 'upscale.exe_path' dans config.yaml"))
        pause()
        return

    role_path = os.path.join(session.projet_chemin, session.role_dossier)
    chapters = list_chapters(role_path)
    if not chapters:
        print(warn("  Aucun chapitre disponible."))
        pause()
        return

    idx = menu("Choisir le chapitre à upscaler", chapters, breadcrumb=session.breadcrumb())
    if idx is None:
        return

    chapter_name = chapters[idx]
    chapter_path = os.path.join(role_path, chapter_name)
    src_path = os.path.join(chapter_path, "01_Original_RAW")
    dst_path = os.path.join(chapter_path, "02_Upscale_RAW")

    images = list_images(src_path)
    if not images:
        print(warn(f"  Aucune image dans 01_Original_RAW/ pour {chapter_name}"))
        pause()
        return

    role_data = read_role_yaml(role_path) or {}
    model = role_data.get("config", {}).get("model_esrgan", "realesrgan-x4plus-anime")
    os.makedirs(dst_path, exist_ok=True)

    print(info(f"\n  Upscale de {len(images)} image(s) — modèle : {model}\n"))
    bar = ProgressBar(len(images), label="Upscale")
    start = time.time()

    for i, img in enumerate(images):
        src_file = os.path.join(src_path, img)
        dst_file = os.path.join(dst_path, img)
        cmd = [exe, "-i", src_file, "-o", dst_file, "-n", model]
        try:
            subprocess.run(cmd, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            print(warn(f"\n  Timeout sur {img}, on continue..."))
        bar.update(i + 1, suffix=img)

    elapsed = time.time() - start
    bar.done()

    result = check_integrity(src_path, dst_path)
    update_integrite(chapter_path, result["raw_count"], result["upscale_count"], result["verified"])

    duree_str = fmt_duration(elapsed)
    mark_etape_done(chapter_path, "upscale", duree=duree_str)

    project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
    add_entry(project_yaml, session.role_label,
              f"{chapter_name} — upscale terminé en {duree_str}")

    if result["verified"]:
        print(ok(f"\n  Upscale terminé en {duree_str}. Intégrité : ✔ ({result['upscale_count']}/{result['raw_count']})"))
    else:
        print(warn(f"\n  Upscale terminé en {duree_str}. Fichiers manquants : {result['missing']}"))
    pause()
