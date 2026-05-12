"""
cmd_004_upscale_realesrgan.py — Upscale via Real-ESRGAN-ncnn-vulkan.
"""
import os
import shutil
import time
import subprocess
from session import session
from config_loader import CFG
from core.role_manager import read_role_yaml, write_role_yaml
from core.status_manager import mark_etape_done, update_integrite
from core.integrity_checker import check_integrity, list_images
from core.changelog import add_entry
from core.project_manager import list_chapters
from ui.colors import ok, err, warn, info
from ui.menu_engine import menu, pause, _clear, prompt_text
from ui.progress_bar import ProgressBar, fmt_duration

LABEL = "⚡  Upscale Real-ESRGAN"
DESCRIPTION = "Lance l'upscale des images RAW via Real-ESRGAN-ncnn-vulkan"


def _get_output_filename(src_filename: str, format_sortie: str) -> str:
    """
    Génère le nom du fichier de sortie avec la bonne extension.
    
    Args:
        src_filename: Nom du fichier source
        format_sortie: Format de sortie (jpg, png, webp)
    
    Returns:
        Nom du fichier avec la nouvelle extension
    """
    stem = os.path.splitext(src_filename)[0]
    return f"{stem}.{format_sortie.lower()}"


def _detect_already_processed(src_path: str, dst_path: str) -> tuple[list[str], list[str]]:
    """
    Détecte les images déjà upscalées.
    
    Returns:
        (images_already_done, images_to_do)
    """
    src_images = list_images(src_path)
    dst_images = list_images(dst_path)
    
    dst_stems = {os.path.splitext(f)[0] for f in dst_images}
    
    already_done = []
    to_do = []
    
    for img in src_images:
        stem = os.path.splitext(img)[0]
        if stem in dst_stems:
            already_done.append(img)
        else:
            to_do.append(img)
    
    return sorted(already_done), sorted(to_do)


def _handle_missing_images(exe: str, src_path: str, dst_path: str, missing: list[str], model: str, format_sortie: str = "png"):
    """
    Gère les images manquantes : propose de traiter ou ignorer chacune.
    
    Args:
        exe: Chemin du Real-ESRGAN
        src_path: Chemin source (01_Original_RAW)
        dst_path: Chemin destination (02_Upscale_RAW)
        missing: Liste des stems manquants
        model: Modèle Real-ESRGAN
        format_sortie: Format de sortie (jpg, png, webp)
    """
    if not missing:
        return
    
    print(warn(f"\n  ⚠️  {len(missing)} image(s) manquante(s)"))
    
    retried = 0
    for stem in missing:
        # Chercher le fichier source correspondant
        src_images = list_images(src_path)
        src_file = None
        for img in src_images:
            if os.path.splitext(img)[0] == stem:
                src_file = os.path.join(src_path, img)
                break
        
        if not src_file:
            print(warn(f"    → {stem} : fichier source introuvable"))
            continue
        
        options = ["Traiter cette image", "Ignorer"]
        idx = menu(
            f"Image manquante : {stem}",
            options,
            breadcrumb=session.breadcrumb() + ["Upscale"],
            allow_escape=False,
            width=50
        )
        
        if idx == 0:  # Traiter
            output_filename = _get_output_filename(os.path.basename(src_file), format_sortie)
            dst_file = os.path.join(dst_path, output_filename)
            cmd = [exe, "-i", src_file, "-o", dst_file, "-n", model, "-f", format_sortie]
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=300, text=True)
                if result.returncode == 0:
                    print(ok(f"    ✔ {stem} — upscalé avec succès"))
                    retried += 1
                else:
                    print(err(f"    ✗ {stem} — erreur lors du traitement"))
            except subprocess.TimeoutExpired:
                print(err(f"    ✗ {stem} — timeout"))
            except Exception as e:
                print(err(f"    ✗ {stem} — {e}"))
        else:  # Ignorer
            print(warn(f"    ↷ {stem} — ignoré"))
    
    if retried > 0:
        print(ok(f"\n  ✔ {retried} image(s) traitée(s) à nouveau"))


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
    format_sortie = role_data.get("config", {}).get("format_sortie_upscale", "png")
    os.makedirs(dst_path, exist_ok=True)
    
    # Menu pour sélectionner le format de sortie
    _clear()
    formats_disponibles = ["jpg", "png", "webp"]
    idx_format = menu(
        "Format de sortie",
        formats_disponibles,
        breadcrumb=session.breadcrumb() + [chapter_name, "Upscale"],
        allow_escape=False,
        width=50
    )
    if idx_format is not None:
        format_sortie = formats_disponibles[idx_format]
        # Sauvegarder le format choisi dans role.yaml
        if "config" not in role_data:
            role_data["config"] = {}
        role_data["config"]["format_sortie_upscale"] = format_sortie
        write_role_yaml(role_path, role_data)

    # Vérifier si un traitement a été interrompu
    already_done, to_do = _detect_already_processed(src_path, dst_path)
    
    if already_done:
        print(info(f"\n  {len(already_done)} image(s) déjà upscalée(s)"))
        print(info(f"  {len(to_do)} image(s) restante(s) à traiter\n"))
        
        options = ["Reprendre (continuer)", "Recommencer (supprimer et refaire)", "Annuler"]
        idx = menu(
            "Traitement précédent détecté",
            options,
            breadcrumb=session.breadcrumb(),
            allow_escape=False,
            width=50
        )
        
        if idx == 2:  # Annuler
            return
        elif idx == 1:  # Recommencer
            shutil.rmtree(dst_path, ignore_errors=True)
            os.makedirs(dst_path, exist_ok=True)
            images_to_process = images
            print(info(f"\n  Dossier 02_Upscale_RAW supprimé. Recommençage...\n"))
        else:  # Reprendre (idx == 0)
            images_to_process = to_do
            if to_do:
                print(info(f"\n  Reprise : {len(to_do)} image(s) à traiter\n"))
            else:
                print(ok(f"\n  ✔ Toutes les images sont déjà upscalées !"))
                pause()
                return
    else:
        images_to_process = images

    print(info(f"  Upscale de {len(images_to_process)} image(s) — modèle : {model}\n"))
    bar = ProgressBar(len(images_to_process), label="Upscale")
    start = time.time()

    for i, img in enumerate(images_to_process):
        src_file = os.path.join(src_path, img)
        output_filename = _get_output_filename(img, format_sortie)
        dst_file = os.path.join(dst_path, output_filename)
        cmd = [exe, "-i", src_file, "-o", dst_file, "-n", model, "-f", format_sortie]
        try:
            subprocess.run(cmd, capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            print(warn(f"\n  Timeout sur {img}, on continue..."))
        bar.update(i + 1, suffix=img)

    elapsed = time.time() - start
    bar.done()

    result = check_integrity(src_path, dst_path)
    
    # Gestion des images manquantes
    if result["missing"]:
        _handle_missing_images(exe, src_path, dst_path, result["missing"], model, format_sortie)
        # Re-vérifier l'intégrité après traitement des images manquantes
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
