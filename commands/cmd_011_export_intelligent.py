"""
cmd_011 — Export intelligent (Slicer webtoon)
----------------------------------------------
Fusionne les images de 03_Clean_JPEG puis découpe intelligemment
le résultat en tranches webtoon (hauteur max configurable).
La coupe cherche une gouttière blanche pour éviter de trancher du dessin.
Génère dans 04_Final_Merged :
  - Webtoon_Slices_PNG/  (optionnel)
  - Webtoon_Slices_JPEG/ (optionnel)
  - NomChapitre_Release.cbz

Valeurs par défaut chargées depuis .role.yaml (section config) :
  - slicer_max_height   (défaut : 8000)
  - slicer_export_png   (défaut : False)
  - slicer_export_jpeg  (défaut : False)
  - slicer_export_cbz   (défaut : True)
  - qscale_global       (défaut : 95)
"""

import os
from datetime import datetime
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Checkbox
from textual.containers import Vertical, Horizontal

LABEL = "Export Intelligent (Slicer)"
DESCRIPTION = (
    "Découpe les images fusionnées en tranches webtoon et génère un CBZ de release"
)


class SlicerConfigModal(ModalScreen):
    DEFAULT_CSS = """
    SlicerConfigModal { align: center middle; }
    #dialog {
        padding: 1 3; background: #1a1a2e;
        border: solid #4a4e69; width: 52; height: auto;
    }
    #lbl_title  { color: #a8dadc; margin-bottom: 1; }
    #lbl_info   { color: #888; margin-bottom: 1; }
    #lbl_error  { color: #ef233c; height: 1; }
    .lbl_champ  { width: 26; }
    .row_champ  { height: auto; margin-bottom: 1; }
    #btn_row    { height: auto; margin-top: 1; }
    """

    def __init__(self, defaults: dict):
        super().__init__()
        self._d = defaults

    def compose(self) -> ComposeResult:
        d = self._d
        with Vertical(id="dialog"):
            yield Label(
                "Slicer webtoon — Export Intelligent", id="lbl_title", classes="title"
            )
            yield Label(
                "Parametres pre-remplis depuis le role actif.\n"
                "Modifiez si besoin avant de lancer.",
                id="lbl_info",
            )
            yield Label("Hauteur max par tranche (px) :")
            with Horizontal(classes="row_champ"):
                yield Label("slicer_max_height :", classes="lbl_champ")
                yield Input(
                    value=str(d.get("slicer_max_height", 8000)),
                    id="inp_height",
                    placeholder="8000",
                )
            yield Label("Formats generes :")
            yield Checkbox(
                "PNG   (lossless)",
                id="chk_png",
                value=bool(d.get("slicer_export_png", False)),
            )
            yield Checkbox(
                "JPEG  (poids reduit)",
                id="chk_jpeg",
                value=bool(d.get("slicer_export_jpeg", False)),
            )
            yield Checkbox(
                "CBZ   (release)",
                id="chk_cbz",
                value=bool(d.get("slicer_export_cbz", True)),
            )
            yield Label("", id="lbl_error")
            with Horizontal(id="btn_row"):
                yield Button("Lancer", id="btn_ok", variant="primary")
                yield Button("Annuler", id="btn_cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
            return
        lbl = self.query_one("#lbl_error", Label)
        try:
            height = int(self.query_one("#inp_height", Input).value.strip())
            if not (1000 <= height <= 65000):
                raise ValueError
        except ValueError:
            lbl.update("Hauteur invalide (1000-65000 px).")
            return
        png = self.query_one("#chk_png", Checkbox).value
        jpeg = self.query_one("#chk_jpeg", Checkbox).value
        cbz = self.query_one("#chk_cbz", Checkbox).value
        if not png and not jpeg and not cbz:
            lbl.update("Selectionnez au moins un format.")
            return
        self.dismiss({"max_height": height, "png": png, "jpeg": jpeg, "cbz": cbz})


def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from core import role_manager, status_manager, changelog, slicer, exporter
    from core.utils import lister_images, run_in_worker
    from ui.screens.screen_progression import ProgressionScreen
    from ui.modals import DangerModal
    from ui.notify import notify_ok, notify_err
    from PIL import Image

    ch_chemin = os.path.join(SESSION.role_dossier, SESSION.chapitre_actif)
    src_dir = os.path.join(ch_chemin, "03_Clean_JPEG")
    dst_dir = os.path.join(ch_chemin, "04_Final_Merged")

    if not os.path.isdir(src_dir) or not os.listdir(src_dir):
        notify_err(app, f"Aucune image dans {src_dir}")
        return

    # Charger les valeurs par defaut depuis .role.yaml
    role_data = role_manager.lire_role(SESSION.role_dossier)
    cfg = role_data.get("config", {})
    defaults = {
        "slicer_max_height": cfg.get("slicer_max_height", 8000),
        "slicer_export_png": cfg.get("slicer_export_png", False),
        "slicer_export_jpeg": cfg.get("slicer_export_jpeg", False),
        "slicer_export_cbz": cfg.get("slicer_export_cbz", True),
        "qscale_global": cfg.get("qscale_global", 95),
    }

    def lancer_avec_config(config):
        if not config:
            return

        max_height = config["max_height"]
        do_png = config["png"]
        do_jpeg = config["jpeg"]
        do_cbz = config["cbz"]
        quality = defaults["qscale_global"]
        images = lister_images(src_dir)

        if not images:
            notify_err(app, "Aucune image trouvee dans 03_Clean_JPEG")
            return

        conflits = [
            f
            for f in (os.listdir(dst_dir) if os.path.isdir(dst_dir) else [])
            if any(f.endswith(ext) for ext in (".png", ".jpg", ".cbz"))
        ]

        def do_export():
            progression_screen = ProgressionScreen(
                titre=f"Export Slicer — {SESSION.chapitre_actif}"
            )
            app.push_screen(progression_screen)

            def worker():
                try:
                    debut = datetime.now()

                    # Fusion verticale
                    app.call_from_thread(
                        progression_screen.set_info, "Fusion des images..."
                    )
                    largeur = hauteur = 0
                    for p in images:
                        with Image.open(p) as img:
                            largeur = max(largeur, img.width)
                            hauteur += img.height
                    canvas = Image.new("RGB", (largeur, hauteur))
                    y = 0
                    for i, p in enumerate(images):
                        with Image.open(p) as img:
                            rgb = img.convert("RGB")
                            canvas.paste(rgb, (0, y))
                            y += rgb.height
                        app.call_from_thread(
                            progression_screen.set_info,
                            f"Fusion : {i + 1}/{len(images)}",
                        )

                    # Decoupe
                    app.call_from_thread(
                        progression_screen.set_info, "Decoupe en tranches..."
                    )
                    slices_list, _ = slicer.slice_image(canvas, max_height)
                    canvas.close()

                    # Export
                    os.makedirs(dst_dir, exist_ok=True)
                    app.call_from_thread(
                        progression_screen.set_info,
                        f"{len(slices_list)} tranche(s) — export en cours...",
                    )
                    result = exporter.exporter_multi_cibles(
                        slices_list,
                        dst_dir,
                        SESSION.chapitre_actif,
                        png=do_png,
                        jpeg=do_jpeg,
                        cbz=do_cbz,
                        jpeg_quality=quality,
                    )

                    duree = str(datetime.now() - debut).split(".")[0]
                    status_manager.marquer_etape(ch_chemin, "export_slicer", duree)
                    changelog.ajouter_entree(
                        SESSION.projet_chemin,
                        SESSION.role_label,
                        f"{SESSION.chapitre_actif} — export slicer "
                        f"({result['slices_count']} tranches) en {duree}",
                    )

                    fmt = " + ".join(
                        f
                        for f, v in [
                            ("PNG", do_png),
                            ("JPEG", do_jpeg),
                            ("CBZ", do_cbz),
                        ]
                        if v
                    )

                    def on_success():
                        progression_screen.dismiss()
                        notify_ok(
                            app,
                            f"Export termine en {duree}\n"
                            f"{result['slices_count']} tranche(s) - {fmt}",
                        )

                    app.call_from_thread(on_success)

                except Exception as e:
                    err = str(e)

                    def on_error():
                        progression_screen.dismiss()
                        notify_err(app, f"Erreur export : {err}")

                    app.call_from_thread(on_error)

            run_in_worker(worker)

        if conflits:
            msg = (
                f"{len(conflits)} fichier(s) existent deja dans 04_Final_Merged :\n"
                + ", ".join(conflits[:5])
                + ("..." if len(conflits) > 5 else "")
                + "\n\nEcraser ?"
            )
            app.push_screen(DangerModal(msg, on_confirm=do_export))
        else:
            do_export()

    app.push_screen(SlicerConfigModal(defaults), lancer_avec_config)
