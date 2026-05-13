"""
cmd_010_surveiller_raw.py — Surveillance en temps réel de 00_Raw/.
Détecte automatiquement nouveaux CBZ et lance pipeline auto : créer chapitre → extraire images.
"""
import os
import re
import time
import threading
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Optional, Callable

from session import session
from core.watcher import RawWatcher
from core.cbz_handler import list_cbz, extract_cbz
from core.project_manager import list_chapters
from core.role_manager import get_sous_dossiers
from core.status_manager import create_status, mark_etape_done, add_note, read_status
from core.changelog import add_entry
from ui.colors import ok, err, warn, info, title, muted
from ui.menu_engine import _clear, menu as prompt_menu, pause
from ui.table_renderer import render_table

LABEL = "👁   Surveiller 00_Raw/ (watcher)"
DESCRIPTION = "Surveillance réactive : crée automatiquement chapitre + extraction au nouveau CBZ"


# ============================================================================
# PHASE 1 : Classes et utilitaires de pipeline
# ============================================================================

class PipelineProgress:
    """Suivi de la progression du pipeline auto-traitement."""

    def __init__(self):
        self.start_time = datetime.now()
        self.steps = {
            "creation_chapitre": {
                "status": "pending",
                "start": None,
                "end": None,
                "message": "",
                "error": None,
            },
            "extraction_images": {
                "status": "pending",
                "start": None,
                "end": None,
                "message": "",
                "error": None,
            },
        }
        self.chapter_name: Optional[str] = None
        self.chapter_path: Optional[str] = None
        self.extracted_count: int = 0
        self.overall_error: Optional[str] = None

    def start_step(self, step_name: str):
        """Marque le début d'une étape."""
        if step_name in self.steps:
            self.steps[step_name]["status"] = "running"
            self.steps[step_name]["start"] = datetime.now()

    def finish_step(self, step_name: str, message: str = "", error: Optional[str] = None):
        """Marque la fin d'une étape."""
        if step_name in self.steps:
            self.steps[step_name]["end"] = datetime.now()
            self.steps[step_name]["status"] = "error" if error else "done"
            self.steps[step_name]["message"] = message
            self.steps[step_name]["error"] = error

    def get_duration(self, step_name: str) -> str:
        """Retourne la durée formatée d'une étape."""
        step = self.steps.get(step_name)
        if not step or not step["start"] or not step["end"]:
            return "—"
        delta = step["end"] - step["start"]
        total_seconds = int(delta.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def is_success(self) -> bool:
        """Retourne True si toutes les étapes sont success."""
        return all(
            s["status"] == "done"
            for s in self.steps.values()
        )


def extract_chapter_number(cbz_name: str) -> Optional[int]:
    """
    Extrait le numéro de chapitre du nom du CBZ.
    Formats supportés:
      - chapitre_42
      - Chapter 42_4dc41b
      - 42_raw.cbz
    Retourne None si aucun numéro trouvé.
    """
    # Format 1: chapitre_NN ou chapter NN[_suffix]
    match = re.search(r'(?:chapitre|chapter)[_\s]+(\d+)', cbz_name, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Format 2: NN_ (au début du nom)
    match = re.search(r'^(\d+)_', cbz_name)
    if match:
        return int(match.group(1))

    return None


def chapter_exists(role_path: str, chapter_num: int) -> bool:
    """Vérifie si un chapitre X existe déjà."""
    chapter_name = f"Chapter {chapter_num:02d}"
    chapter_path = os.path.join(role_path, chapter_name)
    return os.path.isdir(chapter_path)


# ============================================================================
# PHASE 2 : Pipeline automatique
# ============================================================================

def auto_pipeline(
    cbz_name: str,
    chapter_num: int,
    progress: PipelineProgress,
    raw_path: str,
) -> dict:
    """
    Pipeline auto: créer chapitre → extraire images.
    Retourne: {"status": "success|error", "chapter": "Chapter 03", "extracted_count": 142}
    """
    project_path = session.projet_chemin
    role_path = os.path.join(project_path, session.role_dossier)

    # === ÉTAPE 1 : Créer le chapitre ===
    progress.start_step("creation_chapitre")
    try:
        chapter_name = f"Chapter {chapter_num:02d}"
        chapter_path = os.path.join(role_path, chapter_name)

        if os.path.isdir(chapter_path):
            raise ValueError(f"Le chapitre {chapter_name} existe déjà.")

        # Créer dossier et sous-dossiers
        sous_dossiers = get_sous_dossiers(role_path)
        os.makedirs(chapter_path, exist_ok=True)
        for sd in sous_dossiers:
            os.makedirs(os.path.join(chapter_path, sd["nom"]), exist_ok=True)

        # Créer .status.yaml
        create_status(chapter_path, chapter_name, session.role_label)

        # Log dans changelog
        project_yaml = os.path.join(project_path, ".project.yaml")
        add_entry(project_yaml, session.role_label, f"{chapter_name} — dossier créé (auto)")

        progress.chapter_name = chapter_name
        progress.chapter_path = chapter_path
        progress.finish_step("creation_chapitre", f"{chapter_name} créé")

    except Exception as ex:
        progress.finish_step(
            "creation_chapitre",
            error=str(ex)
        )
        progress.overall_error = f"Erreur création chapitre: {str(ex)}"
        return {"status": "error", "error": progress.overall_error}

    # === ÉTAPE 2 : Extraire les images ===
    progress.start_step("extraction_images")
    try:
        cbz_path = os.path.join(raw_path, cbz_name)
        if not os.path.isfile(cbz_path):
            raise FileNotFoundError(f"Archive introuvable: {cbz_path}")

        dest_path = os.path.join(progress.chapter_path, "01_Original_RAW")
        extracted = extract_cbz(cbz_path, dest_path)

        if not extracted:
            raise ValueError("Aucune image extraite (archive vide ou format non supporté)")

        # Marquer l'étape comme done
        mark_etape_done(progress.chapter_path, "extraction_cbz")

        # Log changelog
        add_entry(
            project_yaml,
            session.role_label,
            f"{progress.chapter_name} — extraction CBZ '{cbz_name}' ({len(extracted)} images)"
        )

        # Ajouter note dans .status.yaml
        note = f"Auto-détecté par surveillance [{time.strftime('%H:%M:%S')}] : {len(extracted)} images extraites"
        add_note(progress.chapter_path, note)

        progress.extracted_count = len(extracted)
        progress.finish_step(
            "extraction_images",
            f"{len(extracted)} images extraites"
        )

    except Exception as ex:
        progress.finish_step(
            "extraction_images",
            error=str(ex)
        )
        progress.overall_error = f"Erreur extraction: {str(ex)}"
        return {"status": "error", "error": progress.overall_error}

    return {
        "status": "success",
        "chapter": progress.chapter_name,
        "chapter_path": progress.chapter_path,
        "extracted_count": progress.extracted_count,
    }


# ============================================================================
# PHASE 3 : Affichage et interaction
# ============================================================================

def display_pipeline_progress(progress: PipelineProgress):
    """Affiche un tableau de progression du pipeline."""
    print()
    headers = ["Étape", "Statut", "Durée", "Message"]
    rows = []

    for step_name in ["creation_chapitre", "extraction_images"]:
        step = progress.steps[step_name]
        status_text = ""

        if step["status"] == "done":
            status_text = f"{ok('✔ Done')}"
        elif step["status"] == "error":
            status_text = f"{err('✗ Erreur')}"
        elif step["status"] == "running":
            status_text = f"{warn('⏳ En cours')}"
        else:  # pending
            status_text = f"{muted('– En attente')}"

        duration = progress.get_duration(step_name)
        message = step["error"] if step["error"] else step["message"]

        display_step = step_name.replace("_", " ").title()
        rows.append([display_step, status_text, duration, message])

    table = render_table(headers, rows, col_widths=[25, 20, 12, 40])
    print(table)


def display_post_treatment_menu(progress: PipelineProgress) -> Optional[str]:
    """
    Affiche le menu post-traitement via le menu interactif.
    Retourne: "upscale" | "explorer" | "retour" | "quitter" | None
    """
    if not progress.is_success():
        return "retour"

    print()
    print(ok(f"✔ Pipeline complété : {progress.chapter_name} créé et {progress.extracted_count} images extraites"))
    print()

    options = [
        "Upscale maintenant (cmd_004)",
        "Afficher les images extraites",
        "Retourner à la surveillance",
        "Quitter",
    ]
    choice = prompt_menu(
        "Options post-traitement",
        options,
        breadcrumb=session.breadcrumb(),
        allow_escape=True,
    )

    if choice is None or choice == 2:
        return "retour"
    if choice == 0:
        return "upscale"
    if choice == 1:
        return "explorer"
    if choice == 3:
        return "quitter"
    return "retour"


def open_chapter_explorer(chapter_path: str):
    """Ouvre le dossier du chapitre dans l'explorateur."""
    if sys.platform == "win32":
        subprocess.Popen(["explorer", chapter_path])
    else:
        # Autres OS (à adapter si nécessaire)
        pass


# ============================================================================
# PHASE 4 : Intégration dans la surveillance
# ============================================================================

def on_new_cbz_handler(cbz_name: str, raw_path: str, detected: list):
    """
    Callback de la surveillance.
    Gère: extraction numéro → validation → pipeline auto → menu post-traitement.
    """
    ts = time.strftime("%H:%M:%S")
    detected.append(cbz_name)

    print()
    print(warn(f"  📥 [{ts}] Nouveau RAW détecté: {cbz_name}"))

    # === Extraction et validation du numéro ===
    chapter_num = extract_chapter_number(cbz_name)
    if chapter_num is None:
        print(err(f"  ✗ Impossible d'extraire le numéro du chapitre de '{cbz_name}'"))
        print(info(f"     Format attendu: '*_chapitre_42.cbz' ou '42_raw.cbz'"))
        return

    print(info(f"  → Numéro chapitre détecté: {chapter_num}"))

    # === Vérification: chapitre existe déjà ? ===
    role_path = os.path.join(session.projet_chemin, session.role_dossier)
    if chapter_exists(role_path, chapter_num):
        print(warn(f"  ⚠  Chapitre {chapter_num} existe déjà."))
        print(info("  → Extraction manuelle recommandée (cmd_005)."))
        return

    # === Lancer le pipeline ===
    print(info(f"  → Lancement du pipeline automatique...\n"))
    progress = PipelineProgress()

    result = auto_pipeline(cbz_name, chapter_num, progress, raw_path)

    # === Afficher la progression ===
    display_pipeline_progress(progress)

    # === Gestion des erreurs et menu post-traitement ===
    if result["status"] == "error":
        print(err(f"\n  ✗ {result.get('error', 'Erreur inconnue')}"))
        return

    # Menu post-traitement
    action = display_post_treatment_menu(progress)

    if action == "explorer":
        if progress.chapter_path:
            open_chapter_explorer(progress.chapter_path)
            print(info("  Explorateur ouvert."))
        else:
            print(err("  Chemin du chapitre introuvable, impossible d'ouvrir l'explorateur."))
    elif action == "upscale":
        print(warn("  Upscale automatique : non implémenté (action manuelle recommandée)"))
    elif action == "quitter":
        raise KeyboardInterrupt()
    # "retour" et autres : continuer la surveillance

    print(info(f"  Retour à la surveillance...\n"))


def run():
    _clear()
    raw_path = os.path.join(session.projet_chemin, "00_Raw")

    if not os.path.isdir(raw_path):
        print(err(f"\n  Dossier 00_Raw/ introuvable : {raw_path}"))
        input("  [Entrée] ")
        return

    pending = list_cbz(raw_path)
    print(title(f"\n  👁   Surveillance — {session.projet_nom} / 00_Raw/\n"))
    if pending:
        print(warn(f"  {len(pending)} archive(s) déjà en attente :"))
        for c in pending:
            print(f"    • {c}")
    else:
        print(info("  Aucune archive en attente actuellement."))

    print(info("\n  Surveillance active. Appuyez sur Entrée pour arrêter.\n"))

    detected: list[str] = []
    lock = threading.Lock()

    def on_new_cbz_wrapper(filename: str):
        with lock:
            on_new_cbz_handler(filename, raw_path, detected)

    watcher = RawWatcher(raw_path, on_new_cbz_wrapper)
    watcher.start()

    try:
        input()  # Bloque jusqu'à Entrée
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()

    if detected:
        print(ok(f"\n  Surveillance arrêtée. {len(detected)} CBZ détecté(s) :"))
        for f in detected:
            print(f"    • {f}")
    else:
        print(info("\n  Surveillance arrêtée. Aucun CBZ détecté pendant la session."))
    input("  [Entrée] ")
