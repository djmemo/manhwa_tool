from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Button, LoadingIndicator

class ProgressionScreen(Screen):
    """Écran de progression simple et robuste, sans état partagé avec les threads."""

    DEFAULT_CSS = """
    ProgressionScreen {
        align: center middle;
    }

    #progress_dialog {
        width: 60;
        max-width: 90%;
        height: auto;
        padding: 1 2;
        background: #1a1a2e;
        border: solid #4a4e69;
    }

    #loader {
        width: auto;
        height: auto;
        margin: 1 0;
    }

    #lbl_info {
        margin-bottom: 1;
    }

    #btn_cancel {
        width: 100%;
    }
    """

    def __init__(self, titre: str = "Opération en cours"):
        super().__init__()
        self._titre = titre

    def compose(self) -> ComposeResult:
        with Vertical(id="progress_dialog"):
            yield Label(self._titre, classes="title")
            yield LoadingIndicator(id="loader")
            yield Label("Opération en cours, veuillez patienter...", id="lbl_info", classes="info")
            yield Button("Annuler", id="btn_cancel", variant="error")

    def set_info(self, texte: str) -> None:
        """Met à jour le label d'info. Toujours appelé via app.call_from_thread()."""
        if self.is_mounted:
            try:
                self.query_one("#lbl_info", Label).update(texte)
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss()
