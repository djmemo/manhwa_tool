"""
cmd_008 — Paramètres du rôle
-----------------------------
Permet de modifier les paramètres du rôle actif :
  - Modèle Real-ESRGAN (model_esrgan)
  - Qualité JPEG globale (qscale_global) et par groupe (qscale_groupe)
  - Paramètres Export/Slicer (hauteur max, formats PNG/JPEG/CBZ)
  - Liste des membres (ajout / suppression)
Affiche le changelog du projet en lecture seule.
"""
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import (Label, Button, Input, DataTable,
                              Checkbox, TabbedContent, TabPane)
from textual.containers import VerticalScroll, Horizontal, Vertical

LABEL       = "Paramètres"
DESCRIPTION = "Configuration du rôle actif (modèle, qualité, slicer, membres) et changelog"


class ParamScreen(Screen):
    DEFAULT_CSS = """
    ParamScreen { padding: 1 2; }
    .section-title { color: #a8dadc; text-style: bold; margin-top: 1; margin-bottom: 0; }
    .lbl-champ     { width: 28; }
    .row-champ     { height: auto; margin-bottom: 1; }
    #lbl_feedback  { color: #06d6a0; height: 1; }
    #btn_row       { height: auto; margin-top: 1; }
    #tbl_changelog { height: 12; }
    """

    def compose(self) -> ComposeResult:
        from ui.widgets.breadcrumb import Breadcrumb
        yield Breadcrumb(id="breadcrumb")
        yield Label("⚙️  Paramètres du rôle", classes="title")
        with TabbedContent():

            # ── Onglet 1 : Rôle & Upscale ────────────────────
            with TabPane("🎯 Rôle & Upscale", id="tab_role"):
                with VerticalScroll():
                    yield Label("Modèle Real-ESRGAN :", classes="section-title")
                    with Horizontal(classes="row-champ"):
                        yield Label("model_esrgan :", classes="lbl-champ")
                        yield Input(id="inp_model", placeholder="realesr-animevideov3")

                    yield Label("Qualité JPEG :", classes="section-title")
                    with Horizontal(classes="row-champ"):
                        yield Label("qscale_global (0-100) :", classes="lbl-champ")
                        yield Input(id="inp_qscale_global", placeholder="95")
                    with Horizontal(classes="row-champ"):
                        yield Label("qscale_groupe (0-100) :", classes="lbl-champ")
                        yield Input(id="inp_qscale_groupe", placeholder="90")

                    yield Label("", id="lbl_feedback")
                    with Horizontal(id="btn_row"):
                        yield Button("💾 Sauvegarder", id="btn_save_role", variant="primary")
                        yield Button("Retour",         id="btn_back",      variant="default")

            # ── Onglet 2 : Export & Slicer ────────────────────
            with TabPane("🗜 Export & Slicer", id="tab_slicer"):
                with VerticalScroll():
                    yield Label("Paramètres du Slicer webtoon :", classes="section-title")
                    with Horizontal(classes="row-champ"):
                        yield Label("Hauteur max par tranche (px) :", classes="lbl-champ")
                        yield Input(id="inp_slicer_height", placeholder="8000")

                    yield Label("Formats générés par le pipeline (cmd_006) :", classes="section-title")
                    yield Checkbox("Générer PNG",          id="chk_slicer_png",  value=False)
                    yield Checkbox("Générer JPEG",         id="chk_slicer_jpeg", value=False)
                    yield Checkbox("Générer CBZ (release)", id="chk_slicer_cbz",  value=True)

                    yield Label("", id="lbl_feedback_slicer")
                    with Horizontal():
                        yield Button("💾 Sauvegarder", id="btn_save_slicer", variant="primary")
                        yield Button("Retour",         id="btn_back_slicer", variant="default")

            # ── Onglet 3 : Membres ────────────────────────────
            with TabPane("👥 Membres", id="tab_membres"):
                with VerticalScroll():
                    yield Label("Membres du rôle actif :", classes="section-title")
                    yield DataTable(id="tbl_membres")
                    with Horizontal(classes="row-champ"):
                        yield Input(id="inp_nouveau_membre", placeholder="Nom du membre")
                        yield Button("➕ Ajouter",   id="btn_add_membre",  variant="success")
                        yield Button("🗑 Supprimer", id="btn_del_membre",  variant="error")
                    yield Label("", id="lbl_feedback_membres")
                    with Horizontal():
                        yield Button("💾 Sauvegarder", id="btn_save_membres", variant="primary")
                        yield Button("Retour",         id="btn_back_membres", variant="default")

            # ── Onglet 4 : Changelog ──────────────────────────
            with TabPane("📜 Changelog", id="tab_changelog"):
                with VerticalScroll():
                    yield Label("Historique du projet (lecture seule) :", classes="section-title")
                    yield DataTable(id="tbl_changelog")
                    with Horizontal():
                        yield Button("🔄 Rafraîchir", id="btn_refresh_cl", variant="default")
                        yield Button("Retour",        id="btn_back_cl",    variant="default")

    def on_mount(self) -> None:
        self._charger_role()
        self._charger_changelog()
        self._charger_membres()

    def _charger_role(self) -> None:
        from session import SESSION
        from core import role_manager
        data = role_manager.lire_role(SESSION.role_dossier)
        cfg  = data.get("config", {})
        self.query_one("#inp_model",         Input).value = str(cfg.get("model_esrgan",    "realesr-animevideov3"))
        self.query_one("#inp_qscale_global", Input).value = str(cfg.get("qscale_global",   95))
        self.query_one("#inp_qscale_groupe", Input).value = str(cfg.get("qscale_groupe",   90))
        self.query_one("#inp_slicer_height", Input).value = str(cfg.get("slicer_max_height", 8000))
        self.query_one("#chk_slicer_png",  Checkbox).value = bool(cfg.get("slicer_export_png",  False))
        self.query_one("#chk_slicer_jpeg", Checkbox).value = bool(cfg.get("slicer_export_jpeg", False))
        self.query_one("#chk_slicer_cbz",  Checkbox).value = bool(cfg.get("slicer_export_cbz",  True))

    def _charger_changelog(self) -> None:
        from session import SESSION
        from core import changelog
        tbl = self.query_one("#tbl_changelog", DataTable)
        tbl.clear(columns=True)
        tbl.add_columns("Date", "Rôle", "Action")
        entrees = changelog.lire_changelog(SESSION.projet_chemin, limit=100)
        for e in reversed(entrees):
            tbl.add_row(
                e.get("date",   ""),
                e.get("role",   ""),
                e.get("action", ""))

    def _charger_membres(self) -> None:
        from session import SESSION
        from core import role_manager
        data    = role_manager.lire_role(SESSION.role_dossier)
        membres = data.get("role", {}).get("membres", [])
        tbl = self.query_one("#tbl_membres", DataTable)
        tbl.clear(columns=True)
        tbl.add_column("Membre")
        for m in membres:
            tbl.add_row(str(m))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        from session import SESSION
        from core import role_manager
        from ui.notify import notify_ok, notify_err

        bid = event.button.id

        # ── Retour ──────────────────────────────────────────
        if bid in ("btn_back", "btn_back_slicer", "btn_back_membres", "btn_back_cl"):
            self.app.pop_screen()
            return

        # ── Sauvegarder rôle & upscale ───────────────────────
        if bid == "btn_save_role":
            try:
                data = role_manager.lire_role(SESSION.role_dossier)
                cfg  = data.setdefault("config", {})
                cfg["model_esrgan"]  = self.query_one("#inp_model",         Input).value.strip()
                cfg["qscale_global"] = int(self.query_one("#inp_qscale_global", Input).value or 95)
                cfg["qscale_groupe"] = int(self.query_one("#inp_qscale_groupe", Input).value or 90)
                role_manager.sauvegarder_role(SESSION.role_dossier, data)
                self.query_one("#lbl_feedback", Label).update("✅ Paramètres rôle sauvegardés")
                notify_ok(self.app, "Paramètres rôle sauvegardés.")
            except Exception as e:
                notify_err(self.app, f"Erreur : {e}")
            return

        # ── Sauvegarder slicer ────────────────────────────────
        if bid == "btn_save_slicer":
            try:
                data = role_manager.lire_role(SESSION.role_dossier)
                cfg  = data.setdefault("config", {})
                cfg["slicer_max_height"]  = int(self.query_one("#inp_slicer_height", Input).value or 8000)
                cfg["slicer_export_png"]  = self.query_one("#chk_slicer_png",  Checkbox).value
                cfg["slicer_export_jpeg"] = self.query_one("#chk_slicer_jpeg", Checkbox).value
                cfg["slicer_export_cbz"]  = self.query_one("#chk_slicer_cbz",  Checkbox).value
                role_manager.sauvegarder_role(SESSION.role_dossier, data)
                self.query_one("#lbl_feedback_slicer", Label).update("✅ Paramètres slicer sauvegardés")
                notify_ok(self.app, "Paramètres slicer sauvegardés.")
            except Exception as e:
                notify_err(self.app, f"Erreur : {e}")
            return

        # ── Membres ───────────────────────────────────────────
        if bid == "btn_add_membre":
            nom = self.query_one("#inp_nouveau_membre", Input).value.strip()
            if nom:
                data    = role_manager.lire_role(SESSION.role_dossier)
                membres = data.setdefault("role", {}).setdefault("membres", [])
                if nom not in membres:
                    membres.append(nom)
                    role_manager.sauvegarder_role(SESSION.role_dossier, data)
                    self._charger_membres()
                    self.query_one("#inp_nouveau_membre", Input).value = ""

        if bid == "btn_del_membre":
            tbl = self.query_one("#tbl_membres", DataTable)
            if tbl.cursor_row is not None:
                try:
                    nom  = str(tbl.get_cell_at((tbl.cursor_row, 0)))
                    data = role_manager.lire_role(SESSION.role_dossier)
                    membres = data.get("role", {}).get("membres", [])
                    if nom in membres:
                        membres.remove(nom)
                        role_manager.sauvegarder_role(SESSION.role_dossier, data)
                        self._charger_membres()
                except Exception:
                    pass

        if bid == "btn_save_membres":
            notify_ok(self.app, "Membres sauvegardés.")

        if bid == "btn_refresh_cl":
            self._charger_changelog()


def run(app=None) -> None:
    if not app:
        return
    app.push_screen(ParamScreen())
