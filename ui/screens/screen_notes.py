from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Label, Button, Input, TextArea
from ui.widgets.breadcrumb import Breadcrumb
from core import status_manager
from session import SESSION
import os

class NotesScreen(Screen):
    _current_path = None
    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("📝 Notes de chapitre", classes="title")
        self.lv = ListView()
        yield self.lv
        self.notes_area = TextArea(id="notes_area")
        yield self.notes_area
        self.inp = Input(placeholder="Ajouter une note...", id="note_input")
        yield self.inp
        yield Button("Ajouter note", id="btn_add", variant="primary")
        yield Button("Retour", id="btn_back")
    def on_mount(self):
        if not SESSION.role_dossier: return
        for ch in sorted(os.listdir(SESSION.role_dossier)):
            p = os.path.join(SESSION.role_dossier, ch)
            if os.path.isfile(os.path.join(p, ".status.yaml")):
                self.lv.append(ListItem(Label(ch)))
    def on_list_view_selected(self, event: ListView.Selected):
        ch = str(event.item.query_one(Label).render())
        self._current_path = os.path.join(SESSION.role_dossier, ch)
        st = status_manager.lire_status(self._current_path)
        self.notes_area.load_text(st.get("notes",""))
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back": self.app.pop_screen()
        elif event.button.id == "btn_add" and self._current_path:
            texte = self.inp.value.strip()
            if texte:
                status_manager.mettre_a_jour_notes(self._current_path, texte)
                self.inp.value = ""
