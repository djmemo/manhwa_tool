"""
cmd_003 — Recomposition de pages découpées
-------------------------------------------
Logique :
  Les images de 03_Clean_JPEG sont nommées avec la convention :
      <page>__<partie>.jpg   ex: 001__001.jpg, 001__002.jpg, 001__003.jpg

  Cette commande fusionne verticalement toutes les parties d'une même page
  pour reconstruire l'image originale :
      001__001.jpg + 001__002.jpg + 001__003.jpg  →  001.jpg

  Les images sans séparateur __ sont copiées telles quelles.
  Destination : 04_Final_Merged/
  Format       : choix utilisateur via modale (JPEG / PNG)
  Conflits     : DangerModal si des fichiers existent déjà en destination
"""
import os
from collections import defaultdict
from pathlib import Path as _Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image

from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Checkbox
from textual.containers import Vertical, Horizontal

LABEL       = "Recomposition pages découpées"
DESCRIPTION = "Fusionne les parties __001/__002/... en pages complètes dans 04_Final_Merged"

SEPARATEUR = "__"


# ─────────────────────────────────────────────────────────────────
# Modale de configuration
# ─────────────────────────────────────────────────────────────────
class RecompoConfigModal(ModalScreen[dict | None]):
    DEFAULT_CSS = '''
    RecompoConfigModal { align: center middle; }
    #dialog {
        padding: 1 3;
        background: #1a1a2e;
        border: solid #4a4e69;
        width: 50;
        height: auto;
    }
    #lbl_title   { margin-bottom: 1; color: #a8dadc; }
    #lbl_info    { color: #888; margin-bottom: 1; }
    #lbl_error   { color: #ef233c; height: 1; }
    #btn_row     { height: auto; margin-top: 1; }
    '''

    def __init__(self, nb_groupes: int, nb_pages: int):
        super().__init__()
        self._nb_groupes = nb_groupes
        self._nb_pages   = nb_pages

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("🧩 Recomposition des pages", id="lbl_title", classes="title")
            yield Label(
                f"{self._nb_groupes} page(s) découpée(s) détectée(s)\n"
                f"{self._nb_pages} page(s) sans découpe (copiées telles quelles)",
                id="lbl_info"
            )
            yield Label("Format de sortie :")
            yield Checkbox("JPEG  (recommandé, poids réduit)", id="chk_jpeg", value=True)
            yield Checkbox("PNG   (lossless)",                 id="chk_png",  value=False)
            yield Label("", id="lbl_error")
            with Horizontal(id="btn_row"):
                yield Button("✅ Lancer", id="btn_ok",     variant="primary")
                yield Button("Annuler",   id="btn_cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
            return

        jpeg = self.query_one("#chk_jpeg", Checkbox).value
        png  = self.query_one("#chk_png",  Checkbox).value
        lbl  = self.query_one("#lbl_error", Label)

        if not jpeg and not png:
            lbl.update("⚠️ Sélectionnez au moins un format.")
            return

        self.dismiss({"jpeg": jpeg, "png": png})


# ─────────────────────────────────────────────────────────────────
# Logique métier pure (appelable depuis les tests)
# ─────────────────────────────────────────────────────────────────
def grouper_images(src_dir: str) -> tuple[dict[str, list[str]], list[str]]:
    """
    Scanne src_dir et retourne :
      - groupes  : {nom_base: [chemin_part1, chemin_part2, ...]} triés
      - simples  : [chemin] images sans séparateur __ (copiées telles quelles)
    """
    from core.utils import EXTS_IMAGE
    groupes: dict[str, list[str]] = defaultdict(list)
    simples: list[str] = []

    for f in sorted(os.listdir(src_dir)):
        if not f.lower().endswith(EXTS_IMAGE):
            continue
        stem, ext = os.path.splitext(f)
        if SEPARATEUR in stem:
            base = stem.split(SEPARATEUR)[0]
            groupes[base].append(os.path.join(src_dir, f))
        else:
            simples.append(os.path.join(src_dir, f))

    # Trier les parties de chaque groupe
    for base in groupes:
        groupes[base] = sorted(groupes[base])

    return dict(sorted(groupes.items())), simples


def recomposer_groupe(parties: list[str]) -> "Image":
    """Fusionne verticalement une liste d'images en une seule."""
    from PIL import Image
    images = [Image.open(p).convert("RGB") for p in parties]
    largeur       = max(img.width  for img in images)
    hauteur_totale = sum(img.height for img in images)
    result = Image.new("RGB", (largeur, hauteur_totale))
    y = 0
    for img in images:
        result.paste(img, (0, y))
        y += img.height
    return result


def detecter_conflits(groupes: dict, simples: list[str], dst_dir: str,
                      jpeg: bool, png: bool) -> list[str]:
    """Retourne la liste des fichiers qui seraient écrasés en destination."""
    conflits = []
    exts = ([".jpg"] if jpeg else []) + ([".png"] if png else [])
    for base in groupes:
        for ext in exts:
            p = os.path.join(dst_dir, base + ext)
            if os.path.exists(p):
                conflits.append(os.path.basename(p))
    for src in simples:
        stem = os.path.splitext(os.path.basename(src))[0]
        for ext in exts:
            p = os.path.join(dst_dir, stem + ext)
            if os.path.exists(p):
                conflits.append(os.path.basename(p))
    return conflits


def executer_recomposition(groupes: dict, simples: list[str],
                           dst_dir: str, quality: int,
                           jpeg: bool, png: bool,
                           progress_cb=None) -> dict:
    """
    Effectue la recomposition.
    progress_cb(current, total, msg) appelé après chaque fichier produit.
    """
    from PIL import Image
    os.makedirs(dst_dir, exist_ok=True)
    total   = len(groupes) + len(simples)
    count   = 0
    ecrites = 0

    # 1. Pages découpées → fusionner
    for base, parties in groupes.items():
        img = recomposer_groupe(parties)
        if jpeg:
            p = os.path.join(dst_dir, base + ".jpg")
            img.save(p, "JPEG", quality=quality)
            ecrites += 1
        if png:
            p = os.path.join(dst_dir, base + ".png")
            img.save(p, "PNG")
            ecrites += 1
        count += 1
        if progress_cb:
            progress_cb(count, total, f"Recomposition : {base} ({count}/{total})")

    # 2. Pages simples → copier/convertir
    for src in simples:
        stem = os.path.splitext(os.path.basename(src))[0]
        img  = Image.open(src).convert("RGB")
        if jpeg:
            p = os.path.join(dst_dir, stem + ".jpg")
            img.save(p, "JPEG", quality=quality)
            ecrites += 1
        if png:
            p = os.path.join(dst_dir, stem + ".png")
            img.save(p, "PNG")
            ecrites += 1
        count += 1
        if progress_cb:
            progress_cb(count, total, f"Copie : {stem} ({count}/{total})")

    return {"pages_recomposees": len(groupes), "pages_copiees": len(simples),
            "fichiers_ecrits": ecrites}


# ─────────────────────────────────────────────────────────────────
# Point d'entrée Textual
# ─────────────────────────────────────────────────────────────────
def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from core import role_manager, status_manager, changelog
    from core.utils import run_in_worker
    from ui.screens.screen_progression import ProgressionScreen
    from ui.modals import DangerModal
    from ui.notify import notify_ok, notify_warn, notify_err
    from datetime import datetime

    ch_chemin = os.path.join(SESSION.role_dossier, SESSION.chapitre_actif)
    src_dir   = os.path.join(ch_chemin, "03_Clean_JPEG")
    dst_dir   = os.path.join(ch_chemin, "04_Final_Merged")

    if not os.path.isdir(src_dir) or not os.listdir(src_dir):
        notify_err(app, f"Aucune image dans {src_dir}")
        return

    groupes, simples = grouper_images(src_dir)

    if not groupes and not simples:
        notify_err(app, "Aucune image compatible trouvée dans 03_Clean_JPEG")
        return

    def lancer_avec_config(cfg: dict | None) -> None:
        if not cfg:
            return

        jpeg, png = cfg["jpeg"], cfg["png"]

        role_data = role_manager.lire_role(SESSION.role_dossier)
        quality   = role_data.get("config", {}).get("qscale_global", 95)

        conflits = detecter_conflits(groupes, simples, dst_dir, jpeg, png)

        def do_recomposition() -> None:
            progression_screen = ProgressionScreen(
                titre=f"Recomposition — {SESSION.chapitre_actif}")
            app.push_screen(progression_screen)

            def worker():
                try:
                    debut = datetime.now()

                    def progress_cb(current, total, msg):
                        app.call_from_thread(progression_screen.set_info, msg)

                    res   = executer_recomposition(
                        groupes, simples, dst_dir, quality, jpeg, png, progress_cb)
                    duree = str(datetime.now() - debut).split(".")[0]

                    status_manager.marquer_etape(ch_chemin, "fusion_finale", duree)
                    changelog.ajouter_entree(
                        SESSION.projet_chemin, SESSION.role_label,
                        f"{SESSION.chapitre_actif} — recomposition : "
                        f"{res['pages_recomposees']} pages fusionnées, "
                        f"{res['pages_copiees']} copiées en {duree}"
                    )

                    fmt = " + ".join(
                        f for f, v in [("JPEG", jpeg), ("PNG", png)] if v)

                    def on_success():
                        progression_screen.dismiss()
                        notify_ok(
                            app,
                            f"✅ Recomposition terminée en {duree}\n"
                            f"{res['pages_recomposees']} page(s) fusionnée(s), "
                            f"{res['pages_copiees']} copiée(s) — {fmt}"
                        )
                    app.call_from_thread(on_success)

                except Exception as e:
                    err = str(e)
                    def on_error():
                        progression_screen.dismiss()
                        notify_err(app, f"Erreur recomposition : {err}")
                    app.call_from_thread(on_error)

            run_in_worker(worker)

        if conflits:
            msg = (
                f"⚠️ {len(conflits)} fichier(s) existent déjà dans "
                f"04_Final_Merged :\n"
                + ", ".join(conflits[:5])
                + ("..." if len(conflits) > 5 else "")
                + "\n\nÉcraser ?"
            )
            app.push_screen(DangerModal(msg, on_confirm=do_recomposition))
        else:
            do_recomposition()

    app.push_screen(
        RecompoConfigModal(nb_groupes=len(groupes), nb_pages=len(simples)),
        lancer_avec_config
    )
