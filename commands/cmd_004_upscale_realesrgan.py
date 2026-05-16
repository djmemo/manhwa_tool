"""
cmd_004 — Upscale Real-ESRGAN
------------------------------
Traite chaque image de 01_Original_RAW avec l'exécutable Real-ESRGAN
configuré dans config.yaml (upscale.exe_path).
Le modèle est lu depuis .role.yaml (config.model_esrgan).
Résultats sauvegardés dans 02_Upscale_RAW avec vérification d'intégrité.
"""
import os
import subprocess
from datetime import datetime

LABEL = "Upscale Real-ESRGAN"
DESCRIPTION = 'Améliore la résolution des images RAW via Real-ESRGAN (01_Original_RAW → 02_Upscale_RAW)'
def run(app=None):
    if not app: return

    from session import SESSION
    from config_loader import CFG
    from core import role_manager, status_manager, integrity_checker, changelog
    from ui.screens.screen_progression import ProgressionScreen

    exe_path = CFG.upscale.get("exe_path", "")
    if not os.path.isfile(exe_path):
        from ui.notify import notify_err
        notify_err(app, f"Real-ESRGAN introuvable : {exe_path}\nVérifiez config.yaml")
        return

    ch_chemin = os.path.join(SESSION.role_dossier, SESSION.chapitre_actif)
    src_dir = os.path.join(ch_chemin, "01_Original_RAW")
    dst_dir = os.path.join(ch_chemin, "02_Upscale_RAW")

    role_data = role_manager.lire_role(SESSION.role_dossier)
    model_name = role_data.get("config", {}).get("model_esrgan", "realesr-animevideov3")
    exts = tuple(role_data.get("config", {}).get("extensions_images", [".jpg",".jpeg",".png",".webp"]))

    os.makedirs(dst_dir, exist_ok=True)
    images = sorted(f for f in os.listdir(src_dir) if f.lower().endswith(exts)) if os.path.exists(src_dir) else []

    if not images:
        from ui.notify import notify_err
        notify_err(app, f"Aucune image trouvée dans {src_dir}")
        return

    # 4. Pousser screen_progression
    progression_screen = ProgressionScreen(titre=f"Upscale ({model_name}) - {SESSION.chapitre_actif}")
    app.push_screen(progression_screen)

    def upscale_worker():
        try:
            debut = datetime.now()
            total = len(images)

            for i, img in enumerate(images):
                in_path = os.path.join(src_dir, img)
                out_path = os.path.join(dst_dir, img)

                # 5. Exécution de realesrgan (bloquant dans le thread worker)
                subprocess.run(
                    [exe_path, "-i", in_path, "-o", out_path, "-n", model_name],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                # 6. Mettre à jour la ProgressBar
                app.call_from_thread(
                    progression_screen.set_info,
                    f"Upscale: {img} ({i+1}/{total})"
                )

            duree = str(datetime.now() - debut).split('.')[0]

            # 7 & 8. Vérifier l'intégrité et sauvegarder le résultat
            rapport = integrity_checker.rapport_integrite(src_dir, dst_dir)
            status_manager.mettre_a_jour_integrite(ch_chemin, rapport["raw_count"], rapport["upscale_count"], rapport["verified"])

            # 9. Marquer l'étape upscale
            status_manager.marquer_etape(ch_chemin, "upscale", duree)

            # 10. Ajouter au changelog
            changelog.ajouter_entree(SESSION.projet_chemin, SESSION.role_label, f"{SESSION.chapitre_actif} — upscale en {duree}")

            def on_success():
                progression_screen.dismiss()
                if rapport["verified"]:
                    from ui.notify import notify_ok
                    notify_ok(app, f"Upscale terminé avec succès en {duree}")
                else:
                    from ui.notify import notify_warn
                    notify_warn(app, f"Upscale terminé, mais intégrité échouée ({rapport['upscale_count']}/{rapport['raw_count']})")

            app.call_from_thread(on_success)

        except Exception as e:
            err_msg = str(e)
            def on_error():
                progression_screen.dismiss()
                from ui.notify import notify_err
                notify_err(app, f"Erreur lors de l'upscale : {err_msg}")
            app.call_from_thread(on_error)


    from core.utils import run_in_worker

    run_in_worker(upscale_worker)
