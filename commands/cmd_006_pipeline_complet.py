"""
cmd_006_pipeline_complet.py — Pipeline complet avec reprise intelligente.
Lit .status.yaml, exécute seulement les étapes non faites.
Vérifie la présence d'images avant de confirmer les étapes manuelles.
"""
import os
import re
from session import session
from core.status_manager import read_status, mark_etape_done, is_termine
from core.project_manager import list_chapters, update_project_after_chapter_done
from core.archive_manager import est_archivable, archive_chapter
from core.integrity_checker import count_images
from core.changelog import add_entry
from ui.colors import ok, err, warn, info, title, separator
from ui.menu_engine import menu, pause, _clear

LABEL = "🚀  Pipeline complet"
DESCRIPTION = "Orchestre toutes les étapes d'un chapitre avec reprise intelligente"

ETAPES_ORDER = ["extraction_cbz", "upscale", "nettoyage_psd", "export_jpeg", "fusion_finale"]
ETAPES_LABELS = {
    "extraction_cbz":  "Extraction CBZ                ",
    "upscale":         "Upscale Real-ESRGAN           ",
    "nettoyage_psd":   "Nettoyage PSD  (manuel Photoshop)",
    "export_jpeg":     "Export JPEG    (manuel Photoshop)",
    "fusion_finale":   "Fusion finale                 ",
}
ETAPES_MANUEL = {"nettoyage_psd", "export_jpeg"}
ETAPES_DOSSIER = {
    "nettoyage_psd": "02_Clean_PSD",
    "export_jpeg":   "03_Clean_JPEG",
}
ETAPES_SRC_IMAGES = {
    "extraction_cbz":  "01_Original_RAW",
    "upscale":         "02_Upscale_RAW",
    "nettoyage_psd":   "02_Clean_PSD",
    "export_jpeg":     "03_Clean_JPEG",
    "fusion_finale":   "03_Clean_JPEG",
}


def _print_pipeline_status(chapter_name: str, status: dict, chapter_path: str):
    """Affiche l'état détaillé des étapes avec comptage d'images."""
    print(title(f"\n  🚀  Pipeline — {chapter_name}\n"))
    etapes = status.get("etapes", {})
    for etape in ETAPES_ORDER:
        etape_data = etapes.get(etape, {})
        done = etape_data.get("done", False)
        duree = etape_data.get("duree", "")
        label = ETAPES_LABELS.get(etape, etape)
        extra = f"  ({duree})" if done and duree else ""
        # Compter images dans le dossier source de l'étape
        src_dir = ETAPES_SRC_IMAGES.get(etape, "")
        n_imgs = count_images(os.path.join(chapter_path, src_dir)) if src_dir else 0
        img_hint = f"  [{n_imgs} img]" if n_imgs > 0 else "  [vide]" if not done else ""
        color = "\033[32m" if done else "\033[33m"
        reset = "\033[0m"
        status_txt = "✔ fait" if done else "▶ pend."
        print(f"  {color}{status_txt}{reset}  {label}{extra}{img_hint}")
    integrite = status.get("integrite", {})
    if integrite.get("raw_count", 0) > 0:
        v = "✔" if integrite.get("verified") else "✖"
        print(info(f"\n  Intégrité : {v}  {integrite.get('upscale_count', 0)}/{integrite.get('raw_count', 0)} images"))
    print()


def run():
    _clear()
    role_path = os.path.join(session.projet_chemin, session.role_dossier)
    chapters = list_chapters(role_path)

    if not chapters:
        print(warn("  Aucun chapitre disponible. Créez-en un d'abord."))
        pause()
        return

    idx = menu("Choisir le chapitre", chapters, breadcrumb=session.breadcrumb())
    if idx is None:
        return

    chapter_name = chapters[idx]
    chapter_path = os.path.join(role_path, chapter_name)
    status = read_status(chapter_path)

    if status is None:
        print(err("  .status.yaml introuvable pour ce chapitre."))
        pause()
        return

    _clear()
    _print_pipeline_status(chapter_name, status, chapter_path)
    etapes = status.get("etapes", {})

    for etape in ETAPES_ORDER:
        etape_data = etapes.get(etape, {})

        if etape_data.get("done"):
            continue

        label = ETAPES_LABELS.get(etape, etape).strip()
        print(separator(60))
        print(info(f"\n  ▶  Étape suivante : {label}\n"))

        # ── Étape manuelle ────────────────────────────────────────────────────
        if etape in ETAPES_MANUEL:
            folder_name = ETAPES_DOSSIER[etape]
            folder_path = os.path.join(chapter_path, folder_name)

            # Compter images existantes dans le dossier cible
            n_existing = count_images(folder_path)
            print(info(f"  Dossier : {folder_path}"))
            if n_existing > 0:
                print(ok(f"  {n_existing} image(s) détectée(s) dans {folder_name}/"))
            else:
                print(warn(f"  Dossier vide — effectuez le travail dans Photoshop d'abord."))

            print(f"\n  Confirmez quand '{label}' est terminé [o/N] : ",
                  end="", flush=True)
            ans = input().strip().lower()
            if ans == "o":
                mark_etape_done(chapter_path, etape)
                print(ok(f"  ✔ '{label}' marqué terminé."))
            else:
                print(warn("\n  Pipeline suspendu. Relancez pour reprendre depuis cette étape."))
                pause()
                return

        # ── Extraction CBZ ────────────────────────────────────────────────────
        elif etape == "extraction_cbz":
            from commands.cmd_005_extraction_cbz import run as run_ext
            try:
                run_ext()
            except Exception as e:
                print(err(f"  Erreur extraction : {e}"))
                pause()
                return

        # ── Upscale ───────────────────────────────────────────────────────────
        elif etape == "upscale":
            from commands.cmd_004_upscale_realesrgan import run as run_up
            try:
                run_up()
            except Exception as e:
                print(err(f"  Erreur upscale : {e}"))
                pause()
                return

        # ── Fusion finale ─────────────────────────────────────────────────────
        elif etape == "fusion_finale":
            from commands.cmd_002_fusion_globale import run as run_fus
            try:
                run_fus()
            except Exception as e:
                print(err(f"  Erreur fusion : {e}"))
                pause()
                return

        # Relire le statut après chaque étape automatique
        status = read_status(chapter_path) or status
        etapes = status.get("etapes", {})

    # ── Vérification finale ───────────────────────────────────────────────────
    status = read_status(chapter_path)
    if status and is_termine(status):
        ch_num = _extract_num(chapter_name)
        update_project_after_chapter_done(session.projet_chemin, ch_num)
        project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
        add_entry(project_yaml, session.role_label,
                  f"{chapter_name} — pipeline complet terminé")
        print(separator(60))
        print(ok(f"\n  🎉  {chapter_name} entièrement terminé !\n"))
        print("  Archiver ce chapitre maintenant ? [o/N] : ", end="", flush=True)
        if input().strip().lower() == "o":
            archive_chapter(chapter_path)
    else:
        print(info("\n  Pipeline incomplet — relancez pour reprendre."))

    pause()


def _extract_num(chapter_name: str) -> int:
    m = re.search(r"\d+", chapter_name)
    return int(m.group()) if m else 0
