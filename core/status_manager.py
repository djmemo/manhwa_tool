"""
core/status_manager.py — Gestion de .status.yaml par chapitre.
Responsable de la cohérence des timestamps, statut_global, intégrité et notes.
"""
import os
from datetime import datetime
import yaml


ETAPES_AUTO = {"extraction_cbz", "upscale", "fusion_finale"}
ETAPES_MANUELLES = {"nettoyage_psd", "export_jpeg"}
ALL_ETAPES = ["extraction_cbz", "upscale", "nettoyage_psd", "export_jpeg", "fusion_finale"]

STATUTS = ("non_commence", "en_cours", "termine", "archive")


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _default_status(chapter: str, role: str) -> dict:
    now = _now()
    etapes = {}
    for etape in ALL_ETAPES:
        etapes[etape] = {
            "done": False,
            "date": None,
            "duree": None,
            "auto": etape in ETAPES_AUTO,
        }
    return {
        "chapter": chapter,
        "role": role,
        "created_at": now,
        "updated_at": now,
        "notes": [],
        "etapes": etapes,
        "integrite": {
            "raw_count": 0,
            "upscale_count": 0,
            "verified": False,
        },
        "statut_global": "non_commence",
    }


def create_status(chapter_path: str, chapter: str, role: str) -> dict:
    """Crée un .status.yaml vierge dans le dossier du chapitre."""
    status = _default_status(chapter, role)
    path = os.path.join(chapter_path, ".status.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(status, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return status


def read_status(chapter_path: str) -> dict | None:
    """Lit .status.yaml. Retourne None si absent ou illisible."""
    path = os.path.join(chapter_path, ".status.yaml")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError:
        return None


def write_status(chapter_path: str, status: dict) -> None:
    """Écrit .status.yaml après mise à jour."""
    status["updated_at"] = _now()
    path = os.path.join(chapter_path, ".status.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(status, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def mark_etape_done(chapter_path: str, etape: str, duree: str | None = None) -> dict:
    """Marque une étape comme terminée et recalcule statut_global."""
    status = read_status(chapter_path)
    if status is None:
        raise FileNotFoundError(f".status.yaml introuvable dans {chapter_path}")

    if etape not in status.get("etapes", {}):
        raise ValueError(f"Étape inconnue : {etape}")

    status["etapes"][etape]["done"] = True
    status["etapes"][etape]["date"] = _now()
    if duree:
        status["etapes"][etape]["duree"] = duree

    status["statut_global"] = _calc_statut(status)
    write_status(chapter_path, status)
    return status


def _calc_statut(status: dict) -> str:
    """Recalcule statut_global depuis les étapes."""
    if status.get("statut_global") == "archive":
        return "archive"
    etapes = status.get("etapes", {})
    done_count = sum(1 for e in etapes.values() if e.get("done"))
    total = len(etapes)
    if done_count == 0:
        return "non_commence"
    if done_count == total:
        return "termine"
    return "en_cours"


def calc_progression(status: dict) -> float:
    """Retourne la progression de 0.0 à 1.0."""
    etapes = status.get("etapes", {})
    if not etapes:
        return 0.0
    done = sum(1 for e in etapes.values() if e.get("done"))
    return done / len(etapes)


def is_termine(status: dict) -> bool:
    return status.get("statut_global") == "termine"


def add_note(chapter_path: str, note: str) -> None:
    """Ajoute une note dans .status.yaml > notes."""
    status = read_status(chapter_path)
    if status is None:
        raise FileNotFoundError(f".status.yaml introuvable dans {chapter_path}")
    if "notes" not in status:
        status["notes"] = []
    status["notes"].append({
        "date": _now(),
        "texte": note,
    })
    write_status(chapter_path, status)


def update_integrite(chapter_path: str, raw_count: int, upscale_count: int, verified: bool) -> None:
    """Met à jour le bloc intégrité."""
    status = read_status(chapter_path)
    if status is None:
        raise FileNotFoundError(f".status.yaml introuvable dans {chapter_path}")
    status["integrite"] = {
        "raw_count": raw_count,
        "upscale_count": upscale_count,
        "verified": verified,
    }
    write_status(chapter_path, status)


def mark_archive(chapter_path: str) -> None:
    """Passe le chapitre en statut archive."""
    status = read_status(chapter_path)
    if status is None:
        raise FileNotFoundError(f".status.yaml introuvable dans {chapter_path}")
    status["statut_global"] = "archive"
    write_status(chapter_path, status)
