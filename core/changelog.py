import os
from datetime import datetime
from core.utils import lire_yaml, ecrire_yaml

def ajouter_entree(projet_chemin: str, role: str, action: str) -> None:
    p_file = os.path.join(projet_chemin, ".project.yaml")
    if not os.path.exists(p_file):
        return

    data = lire_yaml(p_file)
    # setdefault NE remplace PAS une valeur None explicite dans le YAML
    # → on force toujours une liste propre si la valeur n'est pas une liste
    if not isinstance(data.get("changelog"), list):
        data["changelog"] = []
    data["changelog"].append({
        "date":   datetime.now().strftime("%Y-%m-%d %H:%M"),
        "role":   role,
        "action": action,
    })
    ecrire_yaml(p_file, data)

def lire_changelog(projet_chemin: str, limit: int = 50) -> list[dict]:
    p_file = os.path.join(projet_chemin, ".project.yaml")
    if not os.path.exists(p_file):
        return []

    data = lire_yaml(p_file)
    changelog = data.get("changelog")
    if not isinstance(changelog, list):
        return []
    return changelog[-limit:]
