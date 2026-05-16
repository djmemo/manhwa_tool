from textual.app import App
from ui.app_css import APP_CSS
from config_loader import CFG
from session import SESSION
import os

class ManhwaApp(App):
    CSS = APP_CSS
    TITLE = "Manhwa Tool v3"
    _watcher_observer = None

    def on_mount(self):
        racine = CFG.racine_scantrad
        if racine and os.path.isdir(racine):
            SESSION.racine_scantrad = racine
            from ui.screens.screen_select_project import SelectProjectScreen
            self.push_screen(SelectProjectScreen())
        else:
            from ui.screens.screen_setup import SetupScreen
            self.push_screen(SetupScreen())

    def on_unmount(self):
        if self._watcher_observer:
            from core.watcher import arreter_watcher
            arreter_watcher(self._watcher_observer)
