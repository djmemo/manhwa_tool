import os
from datetime import datetime
from core.utils import lire_yaml, ecrire_yaml, validate_path

def creer_status(chapitre_chemin: str, chapter: str, role: str) -> dict:
    if not validate_path(chapitre_chemin):
        raise ValueError(f"Chemin de chapitre invalide: {chapitre_chemin}")
    data = {
        "chapter":    chapter,
        "role":       role,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "notes":      "",
        "etapes": {
            "extraction_cbz": {"done": False, "date": None, "duree": None, "auto": True},
            "upscale":        {"done": False, "date": None, "duree": None, "auto": True},
            "nettoyage_psd":  {"done": False, "date": None, "duree": None, "auto": False},
            "export_jpeg":    {"done": False, "date": None, "duree": None, "auto": False},
            "fusion_finale":  {"done": False, "date": None, "duree": None, "auto": True},
        },
        "integrite":     {"raw_count": 0, "upscale_count": 0, "verified": False},
        "statut_global": "en_cours",
    }
    sauvegarder_status(chapitre_chemin, data)
    return data

def lire_status(chapitre_chemin: str) -> dict:
    return lire_yaml(os.path.join(chapitre_chemin, ".status.yaml"))

def sauvegarder_status(chapitre_chemin: str, data: dict) -> None:
    ecrire_yaml(os.path.join(chapitre_chemin, ".status.yaml"), data)

def marquer_etape(chapitre_chemin: str, nom_etape: str, duree: str) -> None:
    try:
        data = lire_status(chapitre_chemin)
    except (FileNotFoundError, ValueError, TypeError) as e:
        print(f"Erreur lors de la lecture du statut: {e}")
        return

    # Vérifier que les données sont bien formées
    if not isinstance(data, dict):
        print("Données de statut corrompues")
        return

    etapes = data.get("etapes")
    if not isinstance(etapes, dict):
        data["etapes"] = {}
        etapes = data["etapes"]

    # Comportement standardisé pour toutes les étapes
    etait_deja_termine = etapes.get(nom_etape, {}).get("done", False)
    etapes[nom_etape] = {
        "done":  True,
        "date":  datetime.now().isoformat(),
        "duree": duree,
    }
    data["updated_at"] = datetime.now().isoformat()

    # Mettre à jour le statut global si toutes les étapes sont terminées
    if not etait_deja_termine and est_chapitre_termine(data):
        data["statut_global"] = "termine"

    sauvegarder_status(chapitre_chemin, data)

def calculer_progression(status: dict) -> float:
    etapes = status.get("etapes") or {}
    if not etapes:
        return 0.0
    return sum(1 for e in etapes.values() if e.get("done")) / len(etapes)

def est_chapitre_termine(status: dict) -> bool:
    etapes = status.get("etapes") or {}
    return bool(etapes) and all(e.get("done", False) for e in etapes.values())

def mettre_a_jour_notes(chapitre_chemin: str, texte: str) -> None:
    data = lire_status(chapitre_chemin)
    notes_actuelles = data.get("notes") or ""
    horodatage = datetime.now().strftime("%Y-%m-%d %H:%M")
    data["notes"] = f"{notes_actuelles}[{horodatage}] {texte}\n"
    sauvegarder_status(chapitre_chemin, data)

def mettre_a_jour_integrite(chapitre_chemin: str, raw_count: int, upscale_count: int, verified: bool) -> None:
    data = lire_status(chapitre_chemin)
    data["integrite"] = {
        "raw_count":     raw_count,
        "upscale_count": upscale_count,
        "verified":      verified,
    }
    sauvegarder_status(chapitre_chemin, data)

def passer_a_statut(chapitre_chemin: str, statut: str) -> None:
    data = lire_status(chapitre_chemin)
    data["statut_global"] = statut
    sauvegarder_status(chapitre_chemin, data)
