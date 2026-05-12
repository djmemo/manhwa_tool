"""
config_loader.py — Chargement de config.yaml et exposition de CFG.
Supporte un chemin de config alternatif via load_config(path).
Expose save_racine() pour persister racine_osirisscan depuis le menu.
"""
import os
import yaml
from dataclasses import dataclass, field


# Chemin canonique du config.yaml (même dossier que ce fichier)
_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
_config_path: str = _DEFAULT_CONFIG_PATH   # peut être surchargé via --config


@dataclass
class MachineConfig:
    racine_osirisscan: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "MachineConfig":
        return cls(racine_osirisscan=d.get("racine_osirisscan", ""))


@dataclass
class UpscaleConfig:
    exe_path: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "UpscaleConfig":
        return cls(exe_path=d.get("exe_path", ""))


@dataclass
class ConsoleConfig:
    largeur_banniere: int = 70

    @classmethod
    def from_dict(cls, d: dict) -> "ConsoleConfig":
        return cls(largeur_banniere=int(d.get("largeur_banniere", 70)))


@dataclass
class AppConfig:
    machine: MachineConfig = field(default_factory=MachineConfig)
    upscale: UpscaleConfig = field(default_factory=UpscaleConfig)
    console: ConsoleConfig = field(default_factory=ConsoleConfig)


def load_config(path: str | None = None) -> "AppConfig":
    global _config_path
    if path is not None:
        _config_path = path
    target = _config_path

    if not os.path.isfile(target):
        return AppConfig()

    with open(target, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return AppConfig(
        machine=MachineConfig.from_dict(raw.get("machine", {})),
        upscale=UpscaleConfig.from_dict(raw.get("upscale", {})),
        console=ConsoleConfig.from_dict(raw.get("console", {})),
    )


def save_racine(new_path: str) -> None:
    """
    Persiste racine_osirisscan dans config.yaml et met à jour CFG en mémoire.
    Préserve toutes les autres clés existantes (upscale, console…).
    """
    global CFG
    target = _config_path

    # Lire le YAML existant pour ne pas écraser les autres sections
    raw: dict = {}
    if os.path.isfile(target):
        with open(target, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    raw.setdefault("machine", {})["racine_osirisscan"] = new_path

    with open(target, "w", encoding="utf-8") as f:
        yaml.dump(raw, f, allow_unicode=True, default_flow_style=False)

    # Mettre à jour le singleton en mémoire
    CFG.machine.racine_osirisscan = new_path


# Singleton chargé au démarrage
CFG: AppConfig = load_config()
