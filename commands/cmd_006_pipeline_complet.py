"""
cmd_006 — Pipeline complet (orchestrateur intelligent)
-------------------------------------------------------
Étapes dans l'ordre :
  1. Extraction CBZ          (auto)
  2. Upscale Real-ESRGAN     (auto)
  3. Nettoyage PSD           (manuel — ouvre explorateur + confirmation)
  4. Export JPEG             (manuel — ouvre explorateur + confirmation)
  7. Export intelligent CBZ  (auto — paramètres par défaut du .role.yaml)
  8. Archivage final         (proposé, refusable)

Comportement :
  - Lit .status.yaml et saute les étapes déjà done: true
  - Écran dédié PipelineScreen avec statut en temps réel
  - Étapes manuelles bloquantes (ouvre explorateur + modale)
  - Archivage proposé en fin (DangerModal, refusable)
"""
import os
import subprocess
import zipfile
from datetime import datetime

LABEL       = "Pipeline Complet"
DESCRIPTION = "Orchestrateur intelligent — reprend le chapitre là où il s'est arrêté"

ETAPES_PIPELINE = [
    ("extraction_cbz",  "Extraction CBZ"),
    ("upscale",         "Upscale Real-ESRGAN"),
    ("nettoyage_psd",   "Nettoyage PSD  [manuel]"),
    ("export_jpeg",     "Export JPEG    [manuel]"),
    ("export_slicer",   "Export intelligent + CBZ"),
    ("archivage",       "Archivage final"),
]


def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from core import (role_manager, status_manager, cbz_handler,
                      integrity_checker, changelog, archive_manager)
    from core.utils import run_in_worker, ouvrir_explorateur
    from config_loader import CFG
    from ui.screens.screen_pipeline import PipelineScreen
    from ui.modals import DangerModal
    from ui.notify import notify_ok, notify_warn, notify_err

    ch_chemin = os.path.join(SESSION.role_dossier, SESSION.chapitre_actif)
    status    = status_manager.lire_status(ch_chemin)
    etapes    = status.get("etapes", {}) if isinstance(status, dict) else {}
    role_data = role_manager.lire_role(SESSION.role_dossier)

    def est_fait(cle: str) -> bool:
        return bool(etapes.get(cle, {}).get("done", False))

    # Construire la liste des étapes à afficher (toutes, même les déjà faites)
    pipeline_screen = PipelineScreen(ETAPES_PIPELINE)
    app.push_screen(pipeline_screen)

    # Pré-marquer les étapes déjà faites (thread principal → appel direct)
    for cle, _ in ETAPES_PIPELINE:
        if cle == "archivage":
            continue
        if est_fait(cle):
            pipeline_screen.mettre_a_jour(cle, "ignore", "déjà fait")

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def maj(cle, statut, detail=""):
        app.call_from_thread(pipeline_screen.mettre_a_jour, cle, statut, detail)

    def etape_auto(cle: str, fn_exec) -> bool:
        """Exécute une étape auto. Retourne True si succès."""
        if est_fait(cle):
            return True
        maj(cle, "en_cours")
        try:
            duree = fn_exec()
            status_manager.marquer_etape(ch_chemin, cle, duree or "auto")
            maj(cle, "ok", duree or "")
            return True
        except Exception as e:
            maj(cle, "erreur", str(e)[:60])
            return False

    # ─────────────────────────────────────────────────────────────
    # Worker principal
    # ─────────────────────────────────────────────────────────────
    def pipeline_worker():

        # ── Étape 1 : Extraction CBZ ──────────────────────────
        if not est_fait("extraction_cbz"):
            maj("extraction_cbz", "en_cours")
            raw_dir = os.path.join(SESSION.projet_chemin, "00_Raw")
            archives = cbz_handler.lister_archives(raw_dir)
            if not archives:
                maj("extraction_cbz", "erreur", "Aucun CBZ dans 00_Raw")
                app.call_from_thread(pipeline_screen.terminer, "❌ Pipeline interrompu")
                return

            # Prendre le CBZ correspondant au chapitre actif si possible
            cible = next(
                (a for a in archives if SESSION.chapitre_actif.split()[-1] in a),
                archives[0]
            )
            archive_path = os.path.join(raw_dir, cible)
            dst_raw = os.path.join(ch_chemin, "01_Original_RAW")
            os.makedirs(dst_raw, exist_ok=True)
            try:
                debut = datetime.now()
                count = cbz_handler.extraire(archive_path, dst_raw)
                duree = str(datetime.now() - debut).split(".")[0]
                status_manager.marquer_etape(ch_chemin, "extraction_cbz", duree)
                maj("extraction_cbz", "ok", f"{count} images · {duree}")
            except Exception as e:
                maj("extraction_cbz", "erreur", str(e)[:60])
                app.call_from_thread(pipeline_screen.terminer, "❌ Pipeline interrompu")
                return

        # ── Étape 2 : Upscale Real-ESRGAN ────────────────────
        if not est_fait("upscale"):
            maj("upscale", "en_cours")
            exe   = CFG.upscale.get("exe_path", "realesrgan-ncnn-vulkan")
            model = role_data.get("config", {}).get("model_esrgan", "realesr-animevideov3")
            src   = os.path.join(ch_chemin, "01_Original_RAW")
            dst   = os.path.join(ch_chemin, "02_Upscale_RAW")
            os.makedirs(dst, exist_ok=True)

            if not os.path.isfile(exe):
                maj("upscale", "erreur", "exe Real-ESRGAN introuvable")
                app.call_from_thread(pipeline_screen.terminer, "❌ Pipeline interrompu")
                return
            try:
                debut  = datetime.now()
                result = subprocess.run(
                    [exe, "-i", src, "-o", dst, "-n", model],
                    capture_output=True, text=True)
                duree  = str(datetime.now() - debut).split(".")[0]
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip()[:80])
                check = integrity_checker.verifier(src, dst)
                status_manager.mettre_a_jour_integrite(
                    ch_chemin, check["raw_count"], check["upscale_count"], check["verified"])
                status_manager.marquer_etape(ch_chemin, "upscale", duree)
                maj("upscale", "ok", duree)
            except Exception as e:
                maj("upscale", "erreur", str(e)[:60])
                app.call_from_thread(pipeline_screen.terminer, "❌ Pipeline interrompu")
                return

        # ── Étape 3 : Nettoyage PSD (manuel) ─────────────────
        if not est_fait("nettoyage_psd"):
            maj("nettoyage_psd", "manuel")
            dossier_psd = os.path.join(ch_chemin, "02_Upscale_RAW")

            import threading
            event_manuel = threading.Event()
            resultat_manuel = {"ok": False}

            def ouvrir_et_confirmer():
                ouvrir_explorateur(dossier_psd)

                class ManuelModal(__import__("textual.screen", fromlist=["ModalScreen"]).ModalScreen):
                    DEFAULT_CSS = """
                    ManuelModal { align: center middle; }
                    #dialog { padding: 1 3; background: #1a1a2e; border: solid #f4a261;
                               width: 55; height: auto; }
                    #lbl_info { color: #f4a261; margin-bottom: 1; }
                    #btn_row  { height: auto; margin-top: 1; }
                    """
                    def compose(self):
                        from textual.widgets import Label, Button
                        from textual.containers import Vertical, Horizontal
                        with Vertical(id="dialog"):
                            yield Label("👋 Étape manuelle — Nettoyage PSD", classes="title")
                            yield Label(
                                f"Dossier ouvert : {dossier_psd}\n\n"
                                "Effectuez le nettoyage dans Photoshop,\n"
                                "puis cliquez sur J'ai terminé.",
                                id="lbl_info")
                            with Horizontal(id="btn_row"):
                                yield Button("✅ J'ai terminé", id="btn_ok",   variant="primary")
                                yield Button("⏭ Passer",       id="btn_skip", variant="default")

                    def on_button_pressed(self, event):
                        resultat_manuel["ok"] = event.button.id == "btn_ok"
                        self.dismiss()
                        event_manuel.set()

                app.push_screen(ManuelModal())

            app.call_from_thread(ouvrir_et_confirmer)
            event_manuel.wait()

            if resultat_manuel["ok"]:
                status_manager.marquer_etape(ch_chemin, "nettoyage_psd", "manuel")
                maj("nettoyage_psd", "ok", "confirmé")
            else:
                maj("nettoyage_psd", "ignore", "passé")

        # ── Étape 4 : Export JPEG (manuel) ───────────────────
        if not est_fait("export_jpeg"):
            maj("export_jpeg", "manuel")
            dossier_jpeg = os.path.join(ch_chemin, "03_Clean_JPEG")
            os.makedirs(dossier_jpeg, exist_ok=True)

            import threading
            event_exp = threading.Event()
            resultat_exp = {"ok": False}

            def ouvrir_et_confirmer_export():
                ouvrir_explorateur(dossier_jpeg)

                class ExportModal(__import__("textual.screen", fromlist=["ModalScreen"]).ModalScreen):
                    DEFAULT_CSS = """
                    ExportModal { align: center middle; }
                    #dialog { padding: 1 3; background: #1a1a2e; border: solid #f4a261;
                               width: 55; height: auto; }
                    #lbl_info { color: #f4a261; margin-bottom: 1; }
                    #btn_row  { height: auto; margin-top: 1; }
                    """
                    def compose(self):
                        from textual.widgets import Label, Button
                        from textual.containers import Vertical, Horizontal
                        with Vertical(id="dialog"):
                            yield Label("👋 Étape manuelle — Export JPEG", classes="title")
                            yield Label(
                                f"Dossier ouvert : {dossier_jpeg}\n\n"
                                "Exportez vos fichiers nettoyés en JPEG\n"
                                "dans ce dossier, puis cliquez sur J'ai terminé.",
                                id="lbl_info")
                            with Horizontal(id="btn_row"):
                                yield Button("✅ J'ai terminé", id="btn_ok",   variant="primary")
                                yield Button("⏭ Passer",       id="btn_skip", variant="default")

                    def on_button_pressed(self, event):
                        resultat_exp["ok"] = event.button.id == "btn_ok"
                        self.dismiss()
                        event_exp.set()

                app.push_screen(ExportModal())

            app.call_from_thread(ouvrir_et_confirmer_export)
            event_exp.wait()

            if resultat_exp["ok"]:
                status_manager.marquer_etape(ch_chemin, "export_jpeg", "manuel")
                maj("export_jpeg", "ok", "confirmé")
            else:
                maj("export_jpeg", "ignore", "passé")

        # ── Étape 7 : Export intelligent Slicer ──────────────
        if not est_fait("export_slicer"):
            maj("export_slicer", "en_cours")
            try:
                from PIL import Image
                from core import slicer, exporter
                from core.utils import lister_images

                src_dir = os.path.join(ch_chemin, "03_Clean_JPEG")
                dst_dir = os.path.join(ch_chemin, "04_Final_Merged")
                images  = lister_images(src_dir)

                if not images:
                    maj("export_slicer", "erreur", "Aucune image dans 03_Clean_JPEG")
                    app.call_from_thread(pipeline_screen.terminer, "❌ Pipeline interrompu")
                    return

                cfg     = role_data.get("config", {})
                max_h   = cfg.get("slicer_max_height", 8000)
                quality = cfg.get("qscale_global", 95)
                do_png  = cfg.get("slicer_export_png",  False)
                do_jpeg = cfg.get("slicer_export_jpeg", False)
                do_cbz  = cfg.get("slicer_export_cbz",  True)

                # Fusionner
                debut = datetime.now()
                largeur = hauteur = 0
                for p in images:
                    with Image.open(p) as img:
                        largeur = max(largeur, img.width)
                        hauteur += img.height

                canvas = Image.new("RGB", (largeur, hauteur))
                y = 0
                for p in images:
                    with Image.open(p) as img:
                        rgb = img.convert("RGB")
                        canvas.paste(rgb, (0, y))
                        y += rgb.height

                slices, _ = slicer.slice_image(canvas, max_h)
                canvas.close()

                os.makedirs(dst_dir, exist_ok=True)
                result = exporter.exporter_multi_cibles(
                    slices, dst_dir, SESSION.chapitre_actif,
                    png=do_png, jpeg=do_jpeg, cbz=do_cbz,
                    jpeg_quality=quality)

                duree = str(datetime.now() - debut).split(".")[0]
                status_manager.marquer_etape(ch_chemin, "export_slicer", duree)
                changelog.ajouter_entree(
                    SESSION.projet_chemin, SESSION.role_label,
                    f"{SESSION.chapitre_actif} — export slicer "
                    f"({result['slices_count']} tranches) en {duree}")
                maj("export_slicer", "ok",
                    f"{result['slices_count']} tranches · {duree}")
            except Exception as e:
                maj("export_slicer", "erreur", str(e)[:60])
                app.call_from_thread(pipeline_screen.terminer, "❌ Pipeline interrompu")
                return

        # ── Fin du pipeline — proposer l'archivage ───────────
        changelog.ajouter_entree(
            SESSION.projet_chemin, SESSION.role_label,
            f"{SESSION.chapitre_actif} — pipeline complet terminé")

        app.call_from_thread(pipeline_screen.terminer, "✅ Pipeline terminé")

        def proposer_archivage():
            import threading
            event_arch = threading.Event()

            class ArchivageModal(__import__("textual.screen", fromlist=["ModalScreen"]).ModalScreen):
                DEFAULT_CSS = """
                ArchivageModal { align: center middle; }
                #dialog { padding: 1 3; background: #2d0000; border: solid #ef233c;
                           width: 52; height: auto; }
                #btn_row { height: auto; margin-top: 1; }
                """
                def compose(self):
                    from textual.widgets import Label, Button
                    from textual.containers import Vertical, Horizontal
                    with Vertical(id="dialog"):
                        yield Label("🗜 Archivage final", classes="title")
                        yield Label(
                            f"Le chapitre {SESSION.chapitre_actif} est terminé.\n"
                            "Voulez-vous l'archiver maintenant ?\n"
                            "(Action irréversible)")
                        with Horizontal(id="btn_row"):
                            yield Button("🗜 Archiver", id="btn_ok",   variant="error")
                            yield Button("Plus tard",   id="btn_skip", variant="default")

                def on_button_pressed(self, event):
                    do_archive = event.button.id == "btn_ok"
                    self.dismiss()
                    if do_archive:
                        try:
                            dst = os.path.join(SESSION.projet_chemin, "_Archives")
                            os.makedirs(dst, exist_ok=True)
                            archive_manager.archiver_chapitre(ch_chemin, dst)
                            changelog.ajouter_entree(
                                SESSION.projet_chemin, SESSION.role_label,
                                f"{SESSION.chapitre_actif} — archivé")
                            notify_ok(app, f"✅ {SESSION.chapitre_actif} archivé.")
                        except Exception as e:
                            notify_err(app, f"Erreur archivage : {e}")

            app.push_screen(ArchivageModal())

        app.call_from_thread(proposer_archivage)

    run_in_worker(pipeline_worker)
