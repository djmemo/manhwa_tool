"""
cmd_005 — Extraction CBZ
-------------------------
Liste les archives .cbz / .zip disponibles dans 00_Raw.
Vérifie l'absence de doublons dans 01_Original_RAW (DangerModal si besoin).
Extrait les images vers le dossier 01_Original_RAW du chapitre actif
et marque l'étape extraction_cbz dans .status.yaml.
"""
import os
from datetime import datetime
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem
from textual.containers import Vertical

LABEL = "Extraction CBZ"
DESCRIPTION = 'Extrait une archive CBZ/ZIP vers 01_Original_RAW du chapitre actif'
class ArchiveSelectionModal(ModalScreen[str]):
    DEFAULT_CSS = '''
    ArchiveSelectionModal { align: center middle; }
    #dialog { padding: 1 2; background: #1a1a2e; border: solid #e94560; width: 60; height: auto; max-height: 80vh; }
    ListView { height: auto; margin-bottom: 1; }
    '''
    def __init__(self, archives: list[str]):
        super().__init__()
        self.archives = archives

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Sélectionnez l'archive à extraire :")
            self.lv = ListView(id="archive_list")
            yield self.lv
            yield Button("Annuler", id="btn_cancel", variant="error")

    def on_mount(self):
        for arc in self.archives:
            self.lv.append(ListItem(Label(arc)))

    def on_list_view_selected(self, event: ListView.Selected):
        self.dismiss(str(event.item.query_one(Label).render()))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_cancel":
            self.dismiss(None)

def run(app=None):
    if not app: return

    from session import SESSION
    from core import cbz_handler, role_manager, status_manager, changelog
    from core.utils import normaliser_nom_chapitre, run_in_worker
    from ui.screens.screen_progression import ProgressionScreen
    from ui.modals import DangerModal
    from ui.notify import notify_warn, notify_ok, notify_err

    raw_chemin = os.path.join(SESSION.projet_chemin, "00_Raw")
    archives = cbz_handler.lister_archives(raw_chemin)

    if not archives:
        notify_warn(app, "Aucune archive CBZ/ZIP trouvée dans 00_Raw/")
        return

    def perform_extraction(archive_name: str):
        nom_chapitre = normaliser_nom_chapitre(archive_name)
        ch_chemin = os.path.join(SESSION.role_dossier, nom_chapitre)
        dst_dir = os.path.join(ch_chemin, "01_Original_RAW")
        archive_path = os.path.join(raw_chemin, archive_name)

        progression_screen = ProgressionScreen(titre=f"Extraction — {nom_chapitre}")
        app.push_screen(progression_screen)

        def extract_worker():
            try:
                debut = datetime.now()

                if not os.path.exists(ch_chemin):
                    role_manager.init_sous_dossiers(SESSION.role_dossier, nom_chapitre)
                    status_manager.creer_status(ch_chemin, nom_chapitre, SESSION.role_label)

                def progress_cb(count, total):
                    app.call_from_thread(progression_screen.set_info, f"Extraction : {count}/{total} images")

                count = cbz_handler.extraire(archive_path, dst_dir, callback=progress_cb)
                duree = str(datetime.now() - debut).split('.')[0]

                status_manager.marquer_etape(ch_chemin, "extraction_cbz", duree)
                changelog.ajouter_entree(
                    SESSION.projet_chemin, SESSION.role_label,
                    f"{nom_chapitre} — {count} images extraites depuis {archive_name} en {duree}"
                )
                SESSION.chapitre_actif = nom_chapitre

                def on_success():
                    progression_screen.dismiss()
                    notify_ok(app, f"✅ {nom_chapitre} extrait : {count} images")
                app.call_from_thread(on_success)

            except Exception as e:
                err_msg = str(e)
                def on_error():
                    progression_screen.dismiss()
                    notify_err(app, f"Erreur d'extraction : {err_msg}")
                app.call_from_thread(on_error)

        run_in_worker(extract_worker)

    def on_archive_selected(archive_name: str | None):
        if not archive_name: return

        nom_chapitre = normaliser_nom_chapitre(archive_name)
        dst_dir = os.path.join(SESSION.role_dossier, nom_chapitre, "01_Original_RAW")

        if cbz_handler.detecter_doublons(os.path.join(raw_chemin, archive_name), dst_dir):
            def on_confirm_overwrite():
                perform_extraction(archive_name)
            app.push_screen(DangerModal(
                f"Des images existent déjà dans {nom_chapitre}/01_Original_RAW.\n"
                "Voulez-vous écraser les fichiers existants ?",
                on_confirm=on_confirm_overwrite
            ))
        else:
            perform_extraction(archive_name)

    app.push_screen(ArchiveSelectionModal(archives), on_archive_selected)
