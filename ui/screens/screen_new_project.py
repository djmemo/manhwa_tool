import os
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input
from textual.containers import Vertical, Horizontal
from ui.widgets.breadcrumb import Breadcrumb
from session import SESSION

class NewProjectScreen(Screen):
    """Écran de création d'un nouveau projet."""

    DEFAULT_CSS = '''
    NewProjectScreen { align: center middle; }
    #dialog {
        padding: 2 4;
        background: #1a1a2e;
        border: double #e94560;
        width: 70;
        height: auto;
    }
    #lbl_title { text-style: bold; color: #e94560; margin-bottom: 1; }
    #lbl_hint  { color: #aaaaaa; margin-bottom: 1; }
    #inp_name  { margin-bottom: 1; }
    #lbl_error { color: #ef233c; height: 1; }
    '''

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Breadcrumb(id="breadcrumb")
            yield Label("➕ Nouveau projet", id="lbl_title", classes="title")
            yield Label(
                "Entrez le nom de votre nouveau projet (oeuvre).\n"
                "Un dossier sera créé dans le répertoire racine.",
                id="lbl_hint"
            )
            yield Label("Nom du projet :")
            yield Input(placeholder="ex: Solo Leveling", id="inp_name")
            yield Label("", id="lbl_error")
            with Horizontal():
                yield Button("✅ Créer", id="btn_ok", variant="primary")
                yield Button("Annuler", id="btn_cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.app.pop_screen()
            return

        nom_projet = self.query_one("#inp_name", Input).value.strip()
        lbl_err = self.query_one("#lbl_error", Label)

        if not nom_projet:
            lbl_err.update("⚠️ Veuillez saisir un nom de projet.")
            return

        projet_chemin = os.path.join(SESSION.racine_scantrad, nom_projet)

        if os.path.exists(projet_chemin):
            lbl_err.update(f"⚠️ Le projet '{nom_projet}' existe déjà.")
            return

        try:
            os.makedirs(projet_chemin, exist_ok=True)
            from core import project_manager
            project_manager.creer_projet(nom_projet, projet_chemin)
            from ui.notify import notify_ok
            notify_ok(self.app, f"✅ Projet '{nom_projet}' créé avec succès.")
            # self.app.pop_screen()
            self.dismiss(True)
        except Exception as e:
            lbl_err.update(f"⚠️ Erreur lors de la création : {e}")