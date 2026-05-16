"""
screen_cbz_alert.py — Alerte CBZ en attente dans 00_Raw/
---------------------------------------------------------
Affiché uniquement quand le rôle "01_Clean" est sélectionné
ET qu'il y a des CBZ non encore extraits dans 00_Raw/.

Comportement :
- Liste les archives avec cases à cocher
- Bouton "Tout cocher / Tout décocher"
- Bouton "Extraire la sélection" → extrait en séquence via cmd_005
- Après extraction complète → switch_screen(MainMenuScreen())
- Escape → pop_screen() (retour à SelectRoleScreen)
"""

import os
import re
from datetime import datetime

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem, Checkbox, Footer
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from ui.widgets.breadcrumb import Breadcrumb
from core import project_manager, cbz_handler, role_manager, status_manager, changelog
from core.utils import normaliser_nom_chapitre, run_in_worker
from session import SESSION


class CbzAlertScreen(Screen):

    BINDINGS = [Binding("escape", "retour", "Retour", show=True)]

    DEFAULT_CSS = """
    CbzAlertScreen { padding: 1 2; }
    #lv_archives  { height: auto; max-height: 14;
                    border: solid #4a4e69; margin-bottom: 1; }
    #btn_row      { height: auto; margin-top: 1; }
    .lbl_archive  { width: 1fr; }
    """

    # ── Compose ───────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("📦 Archives CBZ en attente", classes="title")
        yield Label("", id="lbl_alerte")
        yield ListView(id="lv_archives")
        with Horizontal(id="btn_row"):
            yield Button("☑ Tout cocher", id="btn_toggle", variant="default")
            yield Button(
                "⬇ Extraire", id="btn_extract", variant="warning", disabled=True
            )
            yield Button("⏭ Ignorer", id="btn_ignore", variant="default")
        yield Footer()

    # ── Montage ───────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self._cbz: list[str] = project_manager.detecter_cbz_en_attente(
            SESSION.projet_chemin
        )
        self._all_checked = False

        lv = self.query_one("#lv_archives", ListView)
        lbl = self.query_one("#lbl_alerte", Label)

        n = len(self._cbz)
        lbl.update(
            f"⚠️ {n} archive(s) CBZ détectée(s) dans 00_Raw/ — "
            "cochez celles à extraire."
        )

        for idx, nom in enumerate(self._cbz):
            # ✅ ID safe : index numérique uniquement, pas le nom de fichier
            cb = Checkbox(nom, value=False, id=f"cb_{idx}")
            item = ListItem(cb)
            item._archive_name = nom
            lv.append(item)

    # ── Gestion cases à cocher → activer/désactiver le bouton Extraire ───

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        nb_coches = sum(
            1
            for item in self.query_one("#lv_archives", ListView).children
            if isinstance(item, ListItem) and item.query_one(Checkbox).value
        )
        self.query_one("#btn_extract", Button).disabled = nb_coches == 0

    # ── Boutons ───────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_ignore":
            self._goto_main_menu()

        elif event.button.id == "btn_toggle":
            self._all_checked = not self._all_checked
            label = "☐ Tout décocher" if self._all_checked else "☑ Tout cocher"
            event.button.label = label
            for item in self.query_one("#lv_archives", ListView).children:
                if isinstance(item, ListItem):
                    item.query_one(Checkbox).value = self._all_checked

        elif event.button.id == "btn_extract":
            self._lancer_extractions()

    # ── Extraction en séquence ────────────────────────────────────────────

    def _lancer_extractions(self) -> None:
        """Collecte les archives cochées et les extrait une par une."""
        selection: list[str] = [
            item._archive_name
            for item in self.query_one("#lv_archives", ListView).children
            if isinstance(item, ListItem) and item.query_one(Checkbox).value
        ]
        if not selection:
            return

        # Désactiver les boutons pendant l'extraction
        for btn_id in ("btn_toggle", "btn_extract", "btn_ignore"):
            self.query_one(f"#{btn_id}", Button).disabled = True

        raw_chemin = os.path.join(SESSION.projet_chemin, "00_Raw")

        def worker():
            premier_chapitre: str | None = None  # ✅ capturer le premier

            for archive_name in selection:
                nom_chapitre = normaliser_nom_chapitre(archive_name)
                ch_chemin    = os.path.join(SESSION.role_dossier, nom_chapitre)
                dst_dir      = os.path.join(ch_chemin, "01_Original_RAW")
                archive_path = os.path.join(raw_chemin, archive_name)

                try:
                    debut = datetime.now()

                    if not os.path.exists(ch_chemin):
                        role_manager.init_sous_dossiers(SESSION.role_dossier, nom_chapitre)
                        status_manager.creer_status(ch_chemin, nom_chapitre, SESSION.role_label)

                    def progress_cb(count, total, _nom=nom_chapitre):
                        self.app.call_from_thread(
                            self.query_one("#lbl_alerte", Label).update,
                            f"⏳ {_nom} — {count}/{total} images…",
                        )

                    count = cbz_handler.extraire(archive_path, dst_dir, callback=progress_cb)
                    duree = str(datetime.now() - debut).split(".")[0]

                    status_manager.marquer_etape(ch_chemin, "extraction_cbz", duree)
                    changelog.ajouter_entree(
                        SESSION.projet_chemin, SESSION.role_label,
                        f"{nom_chapitre} — {count} images extraites depuis {archive_name} en {duree}"
                    )

                    # ✅ Mémoriser uniquement le premier chapitre extrait
                    if premier_chapitre is None:
                        premier_chapitre = nom_chapitre

                except Exception as e:
                    from ui.notify import notify_err
                    self.app.call_from_thread(notify_err, self.app, f"Erreur {archive_name} : {e}")

            # ✅ Pointer sur le premier chapitre du groupe, pas le dernier
            if premier_chapitre:
                SESSION.chapitre_actif = premier_chapitre
                role_manager.sauvegarder_chapitre_actif(SESSION.role_dossier, premier_chapitre)

            self.app.call_from_thread(self._goto_main_menu)

        run_in_worker(worker)

    # ── Navigation ────────────────────────────────────────────────────────

    def _goto_main_menu(self) -> None:
        from ui.screens.screen_main_menu import MainMenuScreen

        self.app.switch_screen(MainMenuScreen())

    def action_retour(self) -> None:
        self.app.pop_screen()
