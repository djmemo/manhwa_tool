from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, DataTable
from ui.widgets.breadcrumb import Breadcrumb
from core import changelog
from session import SESSION

class ParametresScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("⚙️  Parametres du role", classes="title")
        yield Input(placeholder="Modele ESRGAN", id="model")
        yield Input(placeholder="qscale_global (ex: 95)", id="qscale_global")
        yield Input(placeholder="qscale_groupe (ex: 90)", id="qscale_groupe")
        yield Button("Sauvegarder", id="btn_save", variant="primary")
        yield Label("Changelog (20 dernieres entrees)", classes="info")
        self.cl_table = DataTable()
        yield self.cl_table
        yield Button("Retour", id="btn_back")
    def on_mount(self):
        self.cl_table.add_columns("Date","Role","Action")
        for e in changelog.lire_changelog(SESSION.projet_chemin, limit=20):
            self.cl_table.add_row(e.get("date",""),e.get("role",""),e.get("action",""))
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.app.pop_screen()
