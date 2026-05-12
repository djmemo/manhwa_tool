"""
core/changelog.py — Gestion append-only du changelog dans .project.yaml.
Ne supprime jamais l'historique existant.
"""
import os
from datetime import datetime
import yaml


def add_entry(project_yaml_path: str, role: str, action: str) -> None:
    """
    Ajoute une entrée au changelog de .project.yaml.
    Append-only : ne modifie jamais les entrées existantes.
    """
    if not os.path.isfile(project_yaml_path):
        raise FileNotFoundError(f".project.yaml introuvable : {project_yaml_path}")

    with open(project_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if "changelog" not in data:
        data["changelog"] = []

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "role": role,
        "action": action,
    }
    data["changelog"].append(entry)

    with open(project_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def read_changelog(project_yaml_path: str) -> list[dict]:
    """Retourne la liste complète des entrées du changelog."""
    if not os.path.isfile(project_yaml_path):
        return []
    with open(project_yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("changelog", [])
