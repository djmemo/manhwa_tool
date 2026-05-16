import os
from session import SESSION
from core.utils import lire_yaml, ecrire_yaml

def creer_role(projet_chemin: str, dossier: str, label: str) -> str:
    role_chemin = os.path.join(projet_chemin, dossier)
    os.makedirs(role_chemin, exist_ok=True)
    data = {
        "role": {"label": label, "dossier": dossier, "membres": []},
        "config": {
            "model_esrgan": "realesr-animevideov3", 
            "qscale_global": 95,
            "qscale_groupe": 90, 
            "extensions_images": [".jpg", ".jpeg", ".png", ".webp"]
        },
        "sous_dossiers": [
            {"index": 0, "nom": "01_Original_RAW"}, 
            {"index": 1, "nom": "02_Upscale_RAW"},
            {"index": 2, "nom": "02_Clean_PSD"},     
            {"index": 3, "nom": "03_Clean_JPEG"},
            {"index": 4, "nom": "04_Final_Merged"},
        ]
    }
    ecrire_yaml(os.path.join(role_chemin, ".role.yaml"), data)
    return role_chemin

def lire_role(role_chemin: str) -> dict:
    return lire_yaml(os.path.join(role_chemin, ".role.yaml"))

def sauvegarder_role(role_chemin: str, data: dict) -> None:
    real_path = os.path.realpath(role_chemin)
    session_real = os.path.realpath(SESSION.role_dossier) if SESSION.role_dossier else ""
    if session_real and not real_path.startswith(session_real):
        raise ValueError(f"Écriture refusée : {role_chemin} est hors du rôle actif.")
    ecrire_yaml(os.path.join(role_chemin, ".role.yaml"), data)

def lister_roles(projet_chemin: str) -> list[dict]:
    roles = []
    if not os.path.exists(projet_chemin):
        return roles
    for d in os.listdir(projet_chemin):
        p = os.path.join(projet_chemin, d)
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, ".role.yaml")):
            roles.append(lire_role(p).get("role", {}))
    return roles

def sauvegarder_chapitre_actif(role_chemin: str, chapitre: str) -> None:
    """Persiste le chapitre actif dans .role.yaml."""
    data = lire_role(role_chemin)
    if not isinstance(data.get("config"), dict):
        data["config"] = {}
    data["config"]["dernier_chapitre_actif"] = chapitre
    ecrire_yaml(os.path.join(role_chemin, ".role.yaml"), data)

def init_sous_dossiers(role_chemin: str, chapitre: str) -> None:
    data = lire_role(role_chemin)
    chap_chemin = os.path.join(role_chemin, chapitre)
    os.makedirs(chap_chemin, exist_ok=True)
    for sd in data.get("sous_dossiers", []):
        os.makedirs(os.path.join(chap_chemin, sd["nom"]), exist_ok=True)

def mettre_a_jour_champ(role_chemin: str, chemin_champ: str, valeur: any) -> None:
    data = lire_role(role_chemin)
    keys = chemin_champ.split(".")
    noeud = data
    for k in keys[:-1]:
        noeud = noeud.setdefault(k, {})
    noeud[keys[-1]] = valeur
    sauvegarder_role(role_chemin, data)
