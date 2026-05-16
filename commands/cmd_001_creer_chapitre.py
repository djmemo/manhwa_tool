"""
cmd_001 — Création d'un nouveau chapitre
-----------------------------------------
Propose le prochain numéro de chapitre (ex: Chapter 085).
Crée l'arborescence complète (01_Original_RAW, 02_Upscale_RAW,
02_Clean_PSD, 03_Clean_JPEG, 04_Final_Merged), initialise le
.status.yaml et met à jour les stats du projet.
"""
import os
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input
from textual.containers import Vertical

LABEL = "Créer un chapitre"
DESCRIPTION = 'Initialise un nouveau chapitre et son arborescence'
class ChapterNameModal(ModalScreen[str]):
    DEFAULT_CSS = '''
    ChapterNameModal { align: center middle; }
    #dialog { padding: 1 2; background: #1a1a2e; border: solid #e94560; width: 40; }
    '''
    def __init__(self, default_name: str):
        super().__init__()
        self.default_name = default_name

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Nom du chapitre à créer :")
            yield Input(value=self.default_name, id="inp_name")
            yield Button("Valider", id="btn_ok", variant="primary")
            yield Button("Annuler", id="btn_cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_ok":
            val = self.query_one("#inp_name", Input).value.strip()
            self.dismiss(val if val else None)
        elif event.button.id == "btn_cancel":
            self.dismiss(None)

def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from core import project_manager, role_manager, status_manager, changelog
    from core.utils import ouvrir_explorateur
    from ui.notify import notify_ok, notify_err

    num_prochain = project_manager.prochain_chapitre(SESSION.projet_chemin)
    default_chapitre = f"Chapter {num_prochain:03d}"

    def on_chapter_name_selected(chapitre: str | None) -> None:
        if not chapitre:
            return

        chapitre_chemin = os.path.join(SESSION.role_dossier, chapitre)
        if os.path.exists(chapitre_chemin):
            notify_err(app, f"Le dossier '{chapitre}' existe déjà !")
            return

        try:
            role_manager.init_sous_dossiers(SESSION.role_dossier, chapitre)
            status_manager.creer_status(chapitre_chemin, chapitre, SESSION.role_label)
            project_manager.mettre_a_jour_progression(SESSION.projet_chemin, num_prochain)
            project_manager.recalculer_stats(SESSION.projet_chemin)
            changelog.ajouter_entree(SESSION.projet_chemin, SESSION.role_label, f"{chapitre} — chapitre créé")

            SESSION.chapitre_actif = chapitre
            # Rafraîchir le fil d'Ariane sur tous les écrans empilés
            for screen in app.screen_stack:
                try:
                    screen.query_one("Breadcrumb").refresh_breadcrumb()
                except Exception:
                    pass
            ouvrir_explorateur(chapitre_chemin)
            notify_ok(app, f"{chapitre} créé avec succès !")
        except Exception as e:
            notify_err(app, f"Erreur lors de la création : {e}")

    app.push_screen(ChapterNameModal(default_chapitre), on_chapter_name_selected)
