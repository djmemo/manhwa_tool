"""
core/project_manager.py — Gestion de .project.yaml et des projets.
Scanner, créer, lire, recalculer stats, détecter CBZ, cumuler temps_upscale.
"""
import os
import re
from datetime import datetime
import yaml

from core.status_manager import read_status


def _now_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _default_project(name: str, racine: str) -> dict:
    return {
        "project": {
            "name": name,
            "created_at": _now_date(),
            "racine_osirisscan": racine,
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
            "derniere_activite": _now_date(),
            "temps_total_upscale": "0:00:00",
        },
        "roles_declares": [],
        "changelog": [],
    }


def scan_projects(racine: str) -> list[dict]:
    """Scanne le dossier racine et retourne les projets (dossier + .project.yaml)."""
    projects = []
    if not os.path.isdir(racine):
        return projects
    for entry in sorted(os.scandir(racine), key=lambda e: e.name):
        if entry.is_dir():
            yaml_path = os.path.join(entry.path, ".project.yaml")
            if os.path.isfile(yaml_path):
                data = read_project_yaml(entry.path)
                projects.append({
                    "nom": data.get("project", {}).get("name", entry.name),
                    "path": entry.path,
                    "dossier": entry.name,
                })
    return projects


def create_project(racine: str, name: str, roles: list[dict] | None = None) -> str:
    """Crée un projet sur disque. Retourne le chemin du projet."""
    from core.role_manager import create_role_yaml, ROLES_DISPONIBLES

    safe = re.sub(r'[<>:"/\\|?*]', "_", name).strip()
    project_path = os.path.join(racine, safe)
    os.makedirs(project_path, exist_ok=True)

    raw_path = os.path.join(project_path, "00_Raw")
    os.makedirs(raw_path, exist_ok=True)

    data = _default_project(name, racine)
    roles_to_create = roles or [ROLES_DISPONIBLES[0]]
    roles_declares = []
    for role_info in roles_to_create:
        role_path = os.path.join(project_path, role_info["dossier"])
        create_role_yaml(role_path, role_info["label"], role_info["dossier"])
        roles_declares.append({"dossier": role_info["dossier"], "label": role_info["label"]})
    data["roles_declares"] = roles_declares

    yaml_path = os.path.join(project_path, ".project.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    return project_path


def read_project_yaml(project_path: str) -> dict:
    path = os.path.join(project_path, ".project.yaml")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_project_yaml(project_path: str, data: dict) -> None:
    path = os.path.join(project_path, ".project.yaml")
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def _parse_duration_to_seconds(duration_str: str) -> float:
    """Parse une durée '1h04m32s' ou '4m32s' ou '0:04:32' en secondes."""
    if not duration_str:
        return 0.0
    # Format H:MM:SS
    m = re.match(r"^(\d+):(\d+):(\d+)$", duration_str)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    # Format Xh Ym Zs
    total = 0.0
    for val, unit in re.findall(r"(\d+(?:\.\d+)?)([hms])", duration_str):
        if unit == "h":
            total += float(val) * 3600
        elif unit == "m":
            total += float(val) * 60
        else:
            total += float(val)
    return total


def _seconds_to_hms(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def recalculate_stats(project_path: str) -> dict:
    """
    Recalcule stats en scannant tous les .status.yaml.
    Cumule temps_total_upscale depuis les durées d'upscale de chaque chapitre.
    """
    data = read_project_yaml(project_path)
    stats = {"chapitres_termines": 0, "chapitres_en_cours": 0, "chapitres_non_commences": 0}
    derniere_activite = data.get("stats", {}).get("derniere_activite", _now_date())
    dernier_termine = data.get("progression", {}).get("dernier_chapitre_termine", 0)
    total_upscale_seconds = 0.0

    for role_dir in _iter_role_dirs(project_path):
        for chapter_dir in _iter_chapter_dirs(role_dir):
            status = read_status(chapter_dir)
            if status is None:
                stats["chapitres_non_commences"] += 1
                continue

            sg = status.get("statut_global", "non_commence")
            if sg == "termine":
                stats["chapitres_termines"] += 1
                ch_num = _extract_chapter_num(os.path.basename(chapter_dir))
                if ch_num > dernier_termine:
                    dernier_termine = ch_num
            elif sg == "en_cours":
                stats["chapitres_en_cours"] += 1
                up_date = status.get("updated_at", "")
                if up_date and up_date[:10] > derniere_activite:
                    derniere_activite = up_date[:10]
            elif sg in ("non_commence", "archive"):
                stats["chapitres_non_commences"] += 1

            # Cumuler temps upscale depuis les étapes
            upscale_etape = status.get("etapes", {}).get("upscale", {})
            if upscale_etape.get("done") and upscale_etape.get("duree"):
                total_upscale_seconds += _parse_duration_to_seconds(upscale_etape["duree"])

    data.setdefault("stats", {}).update(stats)
    data["stats"]["derniere_activite"] = derniere_activite
    data["stats"]["temps_total_upscale"] = _seconds_to_hms(total_upscale_seconds)

    # Mettre à jour chapitres_total_connus = total unique de chapitres scannés
    total_connus = stats["chapitres_termines"] + stats["chapitres_en_cours"] + stats["chapitres_non_commences"]
    data.setdefault("progression", {})["chapitres_total_connus"] = total_connus

    if dernier_termine > 0:
        data["progression"]["dernier_chapitre_termine"] = dernier_termine
        data["progression"]["prochain_chapitre"] = dernier_termine + 1

    write_project_yaml(project_path, data)
    return stats


def get_next_chapter_number(project_path: str) -> int:
    data = read_project_yaml(project_path)
    return data.get("progression", {}).get("prochain_chapitre", 1)


def detect_pending_cbz(project_path: str) -> list[str]:
    raw_path = os.path.join(project_path, "00_Raw")
    if not os.path.isdir(raw_path):
        return []
    return [f for f in sorted(os.listdir(raw_path)) if f.lower().endswith((".cbz", ".zip"))]


def list_chapters(role_path: str) -> list[str]:
    if not os.path.isdir(role_path):
        return []
    return sorted([
        d for d in os.listdir(role_path)
        if os.path.isdir(os.path.join(role_path, d)) and d.lower().startswith("chapter")
    ])


def update_project_after_chapter_done(project_path: str, chapter_num: int) -> None:
    """Met à jour .project.yaml après qu'un chapitre passe en terminé."""
    data = read_project_yaml(project_path)
    prog = data.setdefault("progression", {})
    if chapter_num > prog.get("dernier_chapitre_termine", 0):
        prog["dernier_chapitre_termine"] = chapter_num
        prog["prochain_chapitre"] = chapter_num + 1
    write_project_yaml(project_path, data)
    recalculate_stats(project_path)


def _iter_role_dirs(project_path: str):
    if not os.path.isdir(project_path):
        return
    for entry in os.scandir(project_path):
        if entry.is_dir() and entry.name != "00_Raw" and not entry.name.startswith("."):
            yield entry.path


def _iter_chapter_dirs(role_path: str):
    if not os.path.isdir(role_path):
        return
    for entry in os.scandir(role_path):
        if entry.is_dir() and entry.name.lower().startswith("chapter"):
            yield entry.path


def _extract_chapter_num(chapter_name: str) -> int:
    m = re.search(r"\d+", chapter_name)
    return int(m.group()) if m else 0
