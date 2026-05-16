"""
cmd_010 — Watchdog 00_Raw
--------------------------
Surveille le dossier 00_Raw en tâche de fond (Watchdog).
Dès qu'un nouveau .cbz ou .zip est détecté :
  1. Extraction automatique vers 01_Original_RAW
  2. Upscale automatique via Real-ESRGAN vers 02_Upscale_RAW
  3. Vérification d'intégrité + mise à jour .status.yaml
Relancer la commande pour arrêter le watcher.
"""
import os
import subprocess
from datetime import datetime

LABEL       = "Surveiller RAW"
DESCRIPTION = 'Démarre/Arrête le Watchdog — Auto-Extraction + Auto-Upscale à chaque nouveau CBZ'
def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from core import watcher, changelog
    from ui.notify import notify_ok, notify_warn, notify_err

    # ── Toggle ──────────────────────────────────────────────────
    if app._watcher_observer and app._watcher_observer.is_alive():
        watcher.arreter_watcher(app._watcher_observer)
        app._watcher_observer = None
        changelog.ajouter_entree(SESSION.projet_chemin, SESSION.role_label, "Watchdog arrêté")
        notify_warn(app, "🔴 Watchdog arrêté.")
        return

    raw_dir  = os.path.join(SESSION.projet_chemin, "00_Raw")
    role_dir = SESSION.role_dossier

    if not os.path.exists(raw_dir):
        notify_err(app, f"Dossier 00_Raw introuvable : {raw_dir}")
        return

    from config_loader import CFG
    from core.utils import run_in_worker, normaliser_nom_chapitre
    from core import cbz_handler, status_manager, integrity_checker, role_manager

    def on_new_cbz(archive_path: str) -> None:
        """Callback déclenché par watchdog — s'exécute dans le thread watchdog."""
        archive_name = os.path.basename(archive_path)
        # FIX a) normalisation du nom de chapitre (Chapter 084, pas Chapter 84_f2f748)
        nom_chapitre = normaliser_nom_chapitre(archive_name)
        ch_chemin    = os.path.join(role_dir, nom_chapitre)
        dst_dir      = os.path.join(ch_chemin, "01_Original_RAW")

        try:
            # ── Init dossiers si nécessaire ──────────────────────
            if not os.path.exists(ch_chemin):
                role_manager.init_sous_dossiers(role_dir, nom_chapitre)
                status_manager.creer_status(ch_chemin, nom_chapitre, SESSION.role_label)

            # ── Extraction ───────────────────────────────────────
            # FIX b) archive_path est déjà le chemin complet
            count = cbz_handler.extraire(archive_path, dst_dir)
            status_manager.marquer_etape(ch_chemin, "extraction_cbz", "auto")
            app.call_from_thread(notify_ok, app, f"📦 {nom_chapitre} extrait ({count} images)")

            if count == 0:
                app.call_from_thread(notify_warn, app,
                    f"⚠️ {nom_chapitre} : 0 image extraite — archive vide ou format inconnu ?")
                return

            # ── Upscale automatique ──────────────────────────────
            # FIX c) exe lu depuis CFG (même source que cmd_004)
            exe   = CFG.upscale.get("exe_path", "realesrgan-ncnn-vulkan")
            model = role_manager.lire_role(role_dir).get("config", {}).get(
                        "model_esrgan", "realesr-animevideov3")

            if not os.path.isfile(exe):
                app.call_from_thread(notify_warn, app,
                    f"⚠️ Real-ESRGAN introuvable ({exe}) — upscale ignoré.")
                return

            upscale_dir = os.path.join(ch_chemin, "02_Upscale_RAW")
            os.makedirs(upscale_dir, exist_ok=True)

            debut  = datetime.now()
            result = subprocess.run(
                [exe, "-i", dst_dir, "-o", upscale_dir, "-n", model],
                capture_output=True, text=True
            )
            duree = str(datetime.now() - debut).split(".")[0]

            if result.returncode == 0:
                check = integrity_checker.verifier(dst_dir, upscale_dir)
                status_manager.mettre_a_jour_integrite(
                    ch_chemin, check["raw_count"], check["upscale_count"], check["verified"])
                if check["verified"]:
                    status_manager.marquer_etape(ch_chemin, "upscale", duree)
                    changelog.ajouter_entree(
                        SESSION.projet_chemin, SESSION.role_label,
                        f"{nom_chapitre} — auto-extraction + upscale en {duree}")
                    app.call_from_thread(notify_ok, app, f"✅ {nom_chapitre} upscalé en {duree}")
                else:
                    app.call_from_thread(notify_warn, app,
                        f"⚠️ {nom_chapitre} : intégrité échouée "
                        f"({check['raw_count']} RAW vs {check['upscale_count']} Upscale)")
            else:
                err = result.stderr.strip()[:120] if result.stderr else "inconnu"
                app.call_from_thread(notify_warn, app,
                    f"⚠️ Upscale échoué pour {nom_chapitre} : {err}")

        except Exception as e:
            app.call_from_thread(notify_warn, app, f"Erreur Watchdog sur {nom_chapitre} : {e}")

    # FIX e) on démarre le watcher dans un worker et on stocke l'observer
    # via call_from_thread pour rester thread-safe
    def start_watcher():
        observer = watcher.demarrer_watcher(raw_dir, on_new_cbz)
        app.call_from_thread(setattr, app, "_watcher_observer", observer)

    run_in_worker(start_watcher)
    changelog.ajouter_entree(SESSION.projet_chemin, SESSION.role_label, "Watchdog démarré")
    notify_ok(app, f"🟢 Watchdog actif sur {raw_dir}")
