import os
from textual.app import App
from config_loader import CFG
from session import SESSION
from ui.app_css import APP_CSS
from ui.screens.screen_select_project import SelectProjectScreen
from ui.screens.screen_setup import SetupScreen
from core.watcher import arreter_watcher

class ManhwaApp(App):
    CSS = APP_CSS
    TITLE = "Manhwa Tool v3"
    _watcher_observer = None

    def on_mount(self):
        racine = CFG.racine_scantrad
        if racine and os.path.isdir(racine):
            SESSION.racine_scantrad = racine
            self.push_screen(SelectProjectScreen())
        else:
            self.push_screen(SetupScreen())

    def on_unmount(self):
        if self._watcher_observer:
            arreter_watcher(self._watcher_observer)
