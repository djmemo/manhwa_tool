import os
from datetime import datetime
from core.utils import lire_yaml, ecrire_yaml

def scan_projets(racine: str) -> list[dict]:
    projets = []
    if not os.path.exists(racine):
        return projets
    for d in os.listdir(racine):
        p_path = os.path.join(racine, d)
        if os.path.isdir(p_path) and os.path.isfile(os.path.join(p_path, ".project.yaml")):
            projets.append(lire_projet(p_path))
    return projets

def creer_projet(racine: str, nom: str) -> str:
    p_path = os.path.join(racine, nom)
    os.makedirs(os.path.join(p_path, "00_Raw"), exist_ok=True)
    data = {
        "project": {
            "name": nom,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "racine_scantrad": racine,
        },
        "progression": {
            "dernier_chapitre_termine": 0,
            "prochain_chapitre": 1,
            "chapitres_total_connus": 0,
        },
        "stats": {
            "chapitres_termines": 0,
            "chapitres_en_cours": 0,
            "chapitres_non_commences": 0,
            "derniere_activite": datetime.now().strftime("%Y-%m-%d"),
            "temps_total_upscale": "0:00:00",
        },
        "roles_declares": [],
        "changelog": [],
    }
    sauvegarder_projet(p_path, data)
    return p_path

def lire_projet(projet_chemin: str) -> dict:
    return lire_yaml(os.path.join(projet_chemin, ".project.yaml"))

def sauvegarder_projet(projet_chemin: str, data: dict) -> None:
    ecrire_yaml(os.path.join(projet_chemin, ".project.yaml"), data)

def prochain_chapitre(projet_chemin: str) -> int:
    data = lire_projet(projet_chemin)
    return data.get("progression", {}).get("prochain_chapitre", 1)

def recalculer_stats(projet_chemin: str) -> dict:
    data = lire_projet(projet_chemin)
    termine = en_cours = non_commence = 0

    for dirpath, _, files in os.walk(projet_chemin):
        if ".status.yaml" in files:
            st = lire_yaml(os.path.join(dirpath, ".status.yaml"))
            sg = st.get("statut_global", "")
            if sg == "termine":
                termine += 1
            elif sg == "en_cours":
                en_cours += 1
            else:
                non_commence += 1

    # Guard : stats peut valoir None si le YAML a été corrompu
    if not isinstance(data.get("stats"), dict):
        data["stats"] = {}
    data["stats"].update({
        "chapitres_termines":     termine,
        "chapitres_en_cours":     en_cours,
        "chapitres_non_commences": non_commence,
        "derniere_activite":      datetime.now().strftime("%Y-%m-%d"),
    })
    sauvegarder_projet(projet_chemin, data)
    return data["stats"]

def detecter_cbz_en_attente(projet_chemin: str) -> list[str]:
    raw_dir = os.path.join(projet_chemin, "00_Raw")
    if not os.path.exists(raw_dir):
        return []

    from core.utils import normaliser_nom_chapitre

    cbz_en_attente = []
    for f in sorted(os.listdir(raw_dir)):
        if not f.lower().endswith((".cbz", ".zip")):
            continue

        nom_chapitre = normaliser_nom_chapitre(f)

        # Vérifier dans tous les rôles si 01_Original_RAW existe et contient des images
        deja_extrait = False
        for role_dir in os.listdir(projet_chemin):
            original_raw = os.path.join(projet_chemin, role_dir, nom_chapitre, "01_Original_RAW")
            if os.path.isdir(original_raw) and any(
                fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                for fname in os.listdir(original_raw)
            ):
                deja_extrait = True
                break

        if not deja_extrait:
            cbz_en_attente.append(f)

    return cbz_en_attente

def mettre_a_jour_progression(projet_chemin: str, chapitre_termine: int) -> None:
    data = lire_projet(projet_chemin)
    if not isinstance(data.get("progression"), dict):
        data["progression"] = {}
    data["progression"]["dernier_chapitre_termine"] = chapitre_termine
    data["progression"]["prochain_chapitre"] = chapitre_termine + 1
    sauvegarder_projet(projet_chemin, data)
