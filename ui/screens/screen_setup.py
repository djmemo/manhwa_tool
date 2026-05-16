import os
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input
from textual.containers import Vertical, Horizontal
from ui.widgets.breadcrumb import Breadcrumb

class SetupScreen(Screen):
    """Affiché au premier démarrage si racine_scantrad est absent ou invalide."""

    DEFAULT_CSS = '''
    SetupScreen { align: center middle; }
    #dialog {
        padding: 2 4;
        background: #1a1a2e;
        border: double #e94560;
        width: 70;
        height: auto;
    }
    #lbl_title { text-style: bold; color: #e94560; margin-bottom: 1; }
    #lbl_hint  { color: #aaaaaa; margin-bottom: 1; }
    #inp_path  { margin-bottom: 1; }
    '''

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("⚙️  Configuration initiale — OsirisScan", id="lbl_title")
            yield Label(
                "Indiquez le dossier racine de votre espace de travail OsirisScan.\n"
                "Tous vos projets (oeuvres) seront stockés dans ce dossier.",
                id="lbl_hint"
            )
            yield Label("Chemin du dossier racine :")
            yield Input(placeholder="ex: G:\\scantrad  ou  /home/user/scantrad", id="inp_path")
            yield Label("", id="lbl_error")
            with Horizontal():
                yield Button("✅ Valider", id="btn_ok", variant="primary")
                yield Button("Quitter", id="btn_quit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_quit":
            self.app.exit()
            return

        chemin = self.query_one("#inp_path", Input).value.strip()
        lbl_err = self.query_one("#lbl_error", Label)

        if not chemin:
            lbl_err.update("⚠️ Veuillez saisir un chemin.")
            return

        if not os.path.isdir(chemin):
            try:
                os.makedirs(chemin, exist_ok=True)
            except Exception as e:
                lbl_err.update(f"⚠️ Impossible de créer le dossier : {e}")
                return

        from config_loader import CFG
        from session import SESSION
        CFG.sauvegarder_racine(chemin)
        SESSION.racine_scantrad = chemin

        from ui.screens.screen_select_project import SelectProjectScreen
        self.app.switch_screen(SelectProjectScreen())
