import importlib, importlib.util, glob, os
from core import role_manager
from session import SESSION
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Label, Footer
from textual.binding import Binding
from ui.widgets.breadcrumb import Breadcrumb

def load_commands() -> list:
    commands = []
    pattern = os.path.join(os.path.dirname(__file__), "..", "..", "commands", "cmd_*.py")
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)[:-3]
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "LABEL") and hasattr(mod, "run"): commands.append(mod)
    return commands

class MainMenuScreen(Screen):
    BINDINGS = [Binding("q","quit","Quitter"), Binding("r","refresh","Rafraichir"), Binding("escape","back","Retour")]

    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("📋 Menu Principal", classes="title")
        yield ListView(id="lv_commands")
        yield Footer()

    def on_mount(self):
        self._charger_commandes()
        self._auto_selectionner_chapitre()

    def _auto_selectionner_chapitre(self) -> None:
        from session import SESSION
        import os

        # 1. Déjà défini (ex: juste après extraction) → rien à faire
        if SESSION.chapitre_actif:
            return

        # 2. Trouver le chapitre modifié le plus récemment
        role_dir = SESSION.role_dossier
        if not role_dir or not os.path.isdir(role_dir):
            return

        chapitres = [
            d for d in os.listdir(role_dir)
            if os.path.isdir(os.path.join(role_dir, d))
            and not d.startswith(".")
        ]
        if not chapitres:
            return

        # Trier par date de modification du dossier (le plus récent en premier)
        chapitres.sort(
            key=lambda d: os.path.getmtime(os.path.join(role_dir, d)),
            reverse=True
        )
        SESSION.chapitre_actif = chapitres[0]
        role_manager.sauvegarder_chapitre_actif(SESSION.role_dossier, chapitres[0])
    
    def _charger_commandes(self):
        lv = self.query_one("#lv_commands", ListView)
        lv.clear()                          # ← vider avant de remplir
        self.commands = load_commands()
        for cmd in self.commands:
            item = ListItem(Label(f"[{cmd.LABEL}] - {cmd.DESCRIPTION}"))
            item.cmd_module = cmd
            lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected):
        if hasattr(event.item, "cmd_module"):
            event.item.cmd_module.run(app=self.app)

    def action_back(self):    self.app.pop_screen()
    def action_quit(self):    self.app.exit()
    def action_refresh(self): self._charger_commandes()   # ← appel correct
