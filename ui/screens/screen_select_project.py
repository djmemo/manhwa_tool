import os
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Label, Button
from textual.containers import Horizontal
from ui.widgets.breadcrumb import Breadcrumb
from core import project_manager
from session import SESSION

class SelectProjectScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("🎌 Manhwa Tool v3 — Sélection de l'oeuvre", classes="title")
        yield Label(f"📁 Racine : {SESSION.racine_scantrad}", id="lbl_racine")
        self.lv = ListView()
        yield self.lv
        with Horizontal():
            yield Button("➕ Nouveau projet", id="btn_new", variant="success")
            yield Button("⚙️ Changer de dossier", id="btn_setup", variant="default")
            yield Button("Quitter", id="btn_quit", variant="error")

    def on_mount(self):
        self._charger_projets()

    def _charger_projets(self):
        self.lv.clear()
        projets = project_manager.scan_projets(SESSION.racine_scantrad)
        if not projets:
            self.lv.append(ListItem(Label("Aucun projet trouvé dans ce dossier.")))
        else:
            for p in projets:
                nom = p.get("project", {}).get("name", "Inconnu")
                self.lv.append(ListItem(Label(nom)))

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_quit":
            self.app.exit()
        elif event.button.id == "btn_setup":
            from ui.screens.screen_setup import SetupScreen
            self.app.push_screen(SetupScreen(), callback=lambda _: self._charger_projets())
        elif event.button.id == "btn_new":
            from ui.screens.screen_new_project import NewProjectScreen
            self.app.push_screen(NewProjectScreen(), callback=lambda _: self._charger_projets())

    def on_list_view_selected(self, event: ListView.Selected):
        nom = str(event.item.query_one(Label).render())
        if nom == "Aucun projet trouvé dans ce dossier.":
            return
        SESSION.projet_nom = nom
        SESSION.projet_chemin = os.path.join(SESSION.racine_scantrad, nom)
        from ui.screens.screen_select_role import SelectRoleScreen
        self.app.push_screen(SelectRoleScreen())
