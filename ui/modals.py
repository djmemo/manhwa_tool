from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Button, Label
from textual.containers import Vertical, Horizontal

class ConfirmModal(ModalScreen[bool]):
    DEFAULT_CSS = '''
    ConfirmModal { align: center middle; }
    #dialog {
        padding: 1 3;
        background: #1a1a2e;
        border: solid #4a4e69;
        width: 60;
        height: auto;
    }
    #lbl_msg { margin-bottom: 1; }
    #btn_row { height: auto; }
    '''
    def __init__(self, message: str, on_confirm: callable = None):
        super().__init__()
        self.message = message
        self._on_confirm = on_confirm

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.message, id="lbl_msg")
            with Horizontal(id="btn_row"):
                yield Button("✅ Confirmer", id="btn_confirm", variant="primary")
                yield Button("Annuler",     id="btn_cancel",  variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_confirm":
            # On dismiss EN PREMIER pour vider la pile proprement,
            # puis on exécute le callback une fois l'écran démonté.
            if self._on_confirm:
                self.dismiss(True)
                self.app.call_after_refresh(self._on_confirm)
            else:
                self.dismiss(True)
        elif event.button.id == "btn_cancel":
            self.dismiss(False)


class DangerModal(ConfirmModal):
    DEFAULT_CSS = '''
    DangerModal { align: center middle; }
    #dialog {
        padding: 1 3;
        background: #2d0000;
        border: double #ef233c;
        width: 60;
        height: auto;
    }
    #lbl_msg { color: #ff6b6b; margin-bottom: 1; }
    #btn_row { height: auto; }
    '''
