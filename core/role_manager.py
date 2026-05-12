"""
core/role_manager.py — Gestion de .role.yaml.
Unique point d'entrée pour la configuration des rôles.
"""
import os
from datetime import datetime
import yaml

DEFAULT_SOUS_DOSSIERS = [
    {"nom": "01_Original_RAW", "index": 0, "description": "Images brutes extraites du CBZ"},
    {"nom": "02_Upscale_RAW", "index": 1, "description": "Images upscalées par Real-ESRGAN"},
    {"nom": "02_Clean_PSD", "index": 2, "description": "Fichiers PSD nettoyage manuel"},
    {"nom": "03_Clean_JPEG", "index": 3, "description": "JPEG après export Photoshop"},
    {"nom": "04_Final_Merged", "index": 4, "description": "Image(s) fusionnée(s) finale(s)"},
]

ROLES_DISPONIBLES = [
    {"dossier": "01_Clean", "label": "Cleaner"},
    {"dossier": "02_Translation", "label": "Traducteur"},
    {"dossier": "03_Check", "label": "Correcteur"},
    {"dossier": "04_Edit", "label": "Éditeur"},
    {"dossier": "05_Final", "label": "Final"},
]


def _default_role(label: str, dossier: str) -> dict:
    return {
        "role": {
            "label": label,
            "dossier": dossier,
            "membres": [],
        },
        "config": {
            "model_esrgan": "realesrgan-x4plus-anime",
            "qscale_global": 95,
            "qscale_groupe": 92,
            "extensions_images": ["jpg", "jpeg", "png", "webp"],
        },
        "sous_dossiers": DEFAULT_SOUS_DOSSIERS,
    }


def create_role_yaml(role_path: str, label: str, dossier: str) -> dict:
    """Crée .role.yaml dans le dossier du rôle actif."""
    os.makedirs(role_path, exist_ok=True)
    data = _default_role(label, dossier)
    path = os.path.join(role_path, ".role.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return data


def read_role_yaml(role_path: str) -> dict | None:
    """Lit .role.yaml (lecture seule pour rôles tiers)."""
    path = os.path.join(role_path, ".role.yaml")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return None


def write_role_yaml(role_path: str, data: dict) -> None:
    """Écrit .role.yaml (rôle actif uniquement)."""
    path = os.path.join(role_path, ".role.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def list_roles(project_path: str) -> list[dict]:
    """Liste les rôles disponibles pour un projet (dossiers avec .role.yaml)."""
    roles = []
    for role_info in ROLES_DISPONIBLES:
        role_dir = os.path.join(project_path, role_info["dossier"])
        role_yaml_path = os.path.join(role_dir, ".role.yaml")
        if os.path.isfile(role_yaml_path):
            data = read_role_yaml(role_dir) or {}
            roles.append({
                "dossier": role_info["dossier"],
                "label": data.get("role", {}).get("label", role_info["label"]),
                "path": role_dir,
            })
    return roles


def get_sous_dossiers(role_path: str) -> list[dict]:
    """Retourne la liste des sous-dossiers configurés pour ce rôle."""
    data = read_role_yaml(role_path)
    if data is None:
        return DEFAULT_SOUS_DOSSIERS
    return data.get("sous_dossiers", DEFAULT_SOUS_DOSSIERS)


def update_field(role_path: str, section: str, key: str, value) -> None:
    """Modifie un champ autorisé du rôle actif."""
    data = read_role_yaml(role_path) or {}
    if section not in data:
        data[section] = {}
    data[section][key] = value
    write_role_yaml(role_path, data)


def add_membre(role_path: str, membre: str) -> None:
    data = read_role_yaml(role_path) or {}
    membres = data.get("role", {}).get("membres", [])
    if membre not in membres:
        membres.append(membre)
    data.setdefault("role", {})["membres"] = membres
    write_role_yaml(role_path, data)


def remove_membre(role_path: str, membre: str) -> None:
    data = read_role_yaml(role_path) or {}
    membres = data.get("role", {}).get("membres", [])
    if membre in membres:
        membres.remove(membre)
    data.setdefault("role", {})["membres"] = membres
    write_role_yaml(role_path, data)
