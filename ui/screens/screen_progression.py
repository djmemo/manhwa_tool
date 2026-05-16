from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button, LoadingIndicator

class ProgressionScreen(Screen):
    """Écran de progression simple et robuste, sans état partagé avec les threads."""

    def __init__(self, titre: str = "Opération en cours"):
        super().__init__()
        self._titre = titre

    def compose(self) -> ComposeResult:
        yield Label(self._titre, classes="title")
        yield LoadingIndicator()
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
