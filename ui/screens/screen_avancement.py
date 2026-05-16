from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button
from ui.widgets.breadcrumb import Breadcrumb
from ui.widgets.status_table import StatusTable
from session import SESSION

class AvancementScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("📊 Avancement Global", classes="title")
        self.table = StatusTable()
        yield self.table
        yield Button("Exporter Markdown", id="btn_export", variant="success")
        yield Button("Rafraichir", id="btn_refresh")
        yield Button("Retour", id="btn_back")
    def on_mount(self):
        if SESSION.projet_chemin: self.table.populate(SESSION.projet_chemin)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.app.pop_screen()
        elif event.button.id == "btn_refresh" and SESSION.projet_chemin:
            self.table.populate(SESSION.projet_chemin)
        elif event.button.id == "btn_export":
            import commands.cmd_007_avancement as m
            path = m.exporter_markdown(SESSION.projet_chemin)
            from ui.notify import notify_ok
            notify_ok(self.app, f"Export: {path}")
