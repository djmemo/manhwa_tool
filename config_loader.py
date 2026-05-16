import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")

class _CFG:
    def __init__(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        self.machine = data.get("machine", {})
        self.upscale = data.get("upscale", {})

    @property
    def racine_scantrad(self) -> str:
        return self.machine.get("racine_scantrad", "")

    def sauvegarder_racine(self, chemin: str) -> None:
        """Persiste le chemin racine dans config.yaml."""
        self.machine["racine_scantrad"] = chemin
        data = {
            "machine": self.machine,
            "upscale": self.upscale,
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

CFG = _CFG()
