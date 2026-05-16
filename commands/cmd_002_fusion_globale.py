"""
cmd_002 — Fusion globale
-------------------------
Prend toutes les images de 03_Clean_JPEG et les empile verticalement
dans 04_Final_Merged/merged_output.png.
Le format PNG est utilisé car il n'a pas de limite de hauteur (contrairement au JPEG).
"""
import os
from datetime import datetime
from PIL import Image

LABEL       = "Fusion globale"
DESCRIPTION = "Fusionne toutes les images de 03_Clean_JPEG en un seul PNG sans limite de hauteur"


def _dimensions(images_paths: list[str]) -> tuple[int, int]:
    """Calcule (largeur_max, hauteur_totale) sans tout garder en RAM."""
    largeur, hauteur = 0, 0
    for p in images_paths:
        with Image.open(p) as img:
            largeur = max(largeur, img.width)
            hauteur += img.height
    return largeur, hauteur


def fusionner_images(
    images_paths: list[str],
    out_dir: str,
    app=None,
    pb=None,
) -> str:
    """
    Fusionne verticalement les images en un seul fichier PNG.
    PNG n'a pas de limite de hauteur → pas de découpe nécessaire.
    Retourne le chemin du fichier produit.
    """
    total = len(images_paths)
    largeur, hauteur_totale = _dimensions(images_paths)

    if largeur == 0 or hauteur_totale == 0:
        raise ValueError("Images vides ou illisibles")

    canvas = Image.new("RGB", (largeur, hauteur_totale))
    y = 0

    for i, p in enumerate(images_paths):
        with Image.open(p) as img:
            rgb = img.convert("RGB")
            canvas.paste(rgb, (0, y))
            y += rgb.height
        if pb and app:
            app.call_from_thread(pb.set_info, f"Fusion : {i + 1}/{total}")

    out_path = os.path.join(out_dir, "merged_output.png")
    canvas.save(out_path, "PNG")
    canvas.close()
    return out_path


def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from core import role_manager, status_manager, changelog
    from core.utils import lister_images, run_in_worker
    from ui.screens.screen_progression import ProgressionScreen
    from ui.notify import notify_err, notify_ok

    ch_chemin = os.path.join(SESSION.role_dossier, SESSION.chapitre_actif)
    src_dir   = os.path.join(ch_chemin, "03_Clean_JPEG")
    out_dir   = os.path.join(ch_chemin, "04_Final_Merged")

    os.makedirs(out_dir, exist_ok=True)
    images = lister_images(src_dir)

    if not images:
        notify_err(app, f"Aucune image trouvée dans {src_dir}")
        return

    progression_screen = ProgressionScreen(titre=f"Fusion globale — {SESSION.chapitre_actif}")
    app.push_screen(progression_screen)

    def fusion_worker():
        try:
            debut    = datetime.now()
            out_path = fusionner_images(images, out_dir, app, progression_screen)
            duree    = str(datetime.now() - debut).split(".")[0]

            status_manager.marquer_etape(ch_chemin, "fusion_finale", duree)
            changelog.ajouter_entree(
                SESSION.projet_chemin, SESSION.role_label,
                f"{SESSION.chapitre_actif} — fusion globale en {duree}"
            )

            def on_success():
                progression_screen.dismiss()
                notify_ok(app, f"✅ Fusion terminée en {duree}\n{os.path.basename(out_path)}")

            app.call_from_thread(on_success)

        except Exception as e:
            err = str(e)
            def on_error():
                progression_screen.dismiss()
                notify_err(app, f"Erreur de fusion : {err}")
            app.call_from_thread(on_error)

    run_in_worker(fusion_worker)
