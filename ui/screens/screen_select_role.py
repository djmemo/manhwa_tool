import os
from textual.screen import Screen, ModalScreen
from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Label, Button, Input
from textual.containers import Vertical, Horizontal
from ui.widgets.breadcrumb import Breadcrumb
from core import role_manager
from session import SESSION

ROLES_STANDARDS = [
    ("00_Raw", "Raw"),
    ("01_Clean", "Nettoyage"),
    ("02_Trad", "Traduction"),
    ("03_Check", "Check"),
    ("04_Edit", "Édition"),
    ("05_Final", "Finalisation"),
]


def _scanner_dossiers_orphelins(projet_chemin: str) -> list[str]:
    """Dossiers existants sans .role.yaml, hors exclusions."""
    exclus = {"00_Raw", ".git", "__pycache__"}
    roles_existants = {
        r.get("dossier", "") for r in role_manager.lister_roles(projet_chemin)
    }
    result = []
    if not os.path.isdir(projet_chemin):
        return result
    for entry in sorted(os.listdir(projet_chemin)):
        chemin = os.path.join(projet_chemin, entry)
        if (
            os.path.isdir(chemin)
            and entry not in exclus
            and not entry.startswith(".")
            and entry not in roles_existants
        ):
            result.append(entry)
    return result


class NewRoleModal(ModalScreen[dict | None]):
    """
    Modale de création de rôle.
    - Liste les rôles standards
    - Affiche les dossiers orphelins récupérables (section séparée)
    - Champs libres pour un rôle personnalisé
    FIX : compose() statique — les listes sont remplies dans on_mount()
          IDs tous uniques
    """

    DEFAULT_CSS = """
    NewRoleModal { align: center middle; }
    #dialog {
        padding: 1 3;
        background: #1a1a2e;
        border: solid #4a4e69;
        width: 58;
        height: auto;
        max-height: 85vh;
    }
    #lbl_title        { margin-bottom: 1; color: #a8dadc; }
    #lbl_sub          { color: #888; margin-bottom: 1; }
    #lbl_orphans_hdr  { color: #f4a261; margin-top: 1; margin-bottom: 0; }
    #lbl_custom_hdr   { color: #aaa; margin-top: 1; }
    #lv_standards     { height: auto; max-height: 12; margin-bottom: 0; }
    #lv_orphans       { height: auto; max-height: 6; margin-bottom: 0; }
    #row_custom       { height: auto; margin-bottom: 1; }
    #inp_dossier      { width: 1fr; }
    #inp_label        { width: 1fr; }
    #lbl_error        { color: #ef233c; height: 1; }
    #btn_row          { height: auto; margin-top: 1; }
    """

    def __init__(self, projet_chemin: str):
        super().__init__()
        self._projet_chemin = projet_chemin

    def compose(self) -> ComposeResult:
        # compose() STATIQUE : tous les widgets sont toujours créés
        # → pas de branchement conditionnel, pas d'ID dupliqué
        with Vertical(id="dialog"):
            yield Label("➕ Nouveau rôle", id="lbl_title", classes="title")
            yield Label("Sélectionnez un rôle standard :", id="lbl_sub")
            yield ListView(id="lv_standards")

            yield Label(
                "🔧 Dossiers existants sans configuration :", id="lbl_orphans_hdr"
            )
            yield ListView(id="lv_orphans")

            yield Label("— Ou personnalisé —", id="lbl_custom_hdr")
            with Horizontal(id="row_custom"):
                yield Input(placeholder="Dossier (ex: 06_Extra)", id="inp_dossier")
                yield Input(placeholder="Label (ex: Extra)", id="inp_label")

            yield Label("", id="lbl_error")
            with Horizontal(id="btn_row"):
                yield Button("✅ Créer", id="btn_ok", variant="primary")
                yield Button("Annuler", id="btn_cancel", variant="default")

    def on_mount(self) -> None:
        roles_existants = {
            r.get("dossier", "") for r in role_manager.lister_roles(self._projet_chemin)
        }

        # Rôles standards
        lv_std = self.query_one("#lv_standards", ListView)
        for dossier, label in ROLES_STANDARDS:
            if dossier in roles_existants:
                item = ListItem(Label(f"✅ {dossier}  —  {label}  [déjà configuré]"))
                item._disabled_role = True
            else:
                item = ListItem(Label(f"{dossier}  —  {label}"))
                item._disabled_role = False
            item._role_dossier = dossier
            item._role_label = label
            lv_std.append(item)

        # Dossiers orphelins
        lv_orp = self.query_one("#lv_orphans", ListView)
        lbl_orp = self.query_one("#lbl_orphans_hdr", Label)
        orphelins = _scanner_dossiers_orphelins(self._projet_chemin)
        if orphelins:
            for entry in orphelins:
                item = ListItem(Label(f"🔧 {entry}  —  (récupérer)"))
                item._disabled_role = False
                item._role_dossier = entry
                item._role_label = entry
                lv_orp.append(item)
        else:
            # Cacher proprement si aucun orphelin
            lbl_orp.display = False
            lv_orp.display = False

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if getattr(event.item, "_disabled_role", False):
            return
        self.query_one("#inp_dossier", Input).value = event.item._role_dossier
        self.query_one("#inp_label", Input).value = event.item._role_label
        self.query_one("#lbl_error", Label).update("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_cancel":
            self.dismiss(None)
            return

        dossier = self.query_one("#inp_dossier", Input).value.strip()
        label = self.query_one("#inp_label", Input).value.strip()
        lbl_err = self.query_one("#lbl_error", Label)

        if not dossier:
            lbl_err.update("⚠️ Le nom du dossier est obligatoire.")
            return
        if not label:
            lbl_err.update("⚠️ Le label est obligatoire.")
            return

        role_yaml = os.path.join(self._projet_chemin, dossier, ".role.yaml")
        if os.path.isfile(role_yaml):
            lbl_err.update(f"⚠️ '{dossier}' est déjà un rôle configuré.")
            return

        self.dismiss({"dossier": dossier, "label": label})


class SelectRoleScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("👤 Sélection du rôle actif", classes="title")
        self.lv = ListView()
        yield self.lv
        with Horizontal():
            yield Button("➕ Nouveau rôle", id="btn_new", variant="success")
            yield Button("Retour", id="btn_back", variant="default")

    def on_mount(self):
        self._charger_roles()

    def _charger_roles(self):
        self.lv.clear()
        roles = role_manager.lister_roles(SESSION.projet_chemin)
        if not roles:
            self.lv.append(ListItem(Label("Aucun rôle configuré — créez-en un.")))
            return
        for r in roles:
            item = ListItem(Label(f"{r.get('dossier','')}  ---  {r.get('label','')}"))
            item._role_data = r
            self.lv.append(item)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_back":
            self.app.pop_screen()
        elif event.button.id == "btn_new":

            def on_created(result: dict | None):
                if not result:
                    return
                try:
                    role_manager.creer_role(
                        SESSION.projet_chemin,
                        result["dossier"],
                        result["label"],
                    )
                    from ui.notify import notify_ok

                    notify_ok(self.app, f"✅ Rôle '{result['label']}' créé.")
                    self._charger_roles()
                except Exception as e:
                    from ui.notify import notify_err

                    notify_err(self.app, f"Erreur création rôle : {e}")

            self.app.push_screen(NewRoleModal(SESSION.projet_chemin), on_created)

    def on_list_view_selected(self, event: ListView.Selected):
        if not hasattr(event.item, "_role_data"):
            return
        r = event.item._role_data

        SESSION.role_dossier = os.path.join(SESSION.projet_chemin, r.get("dossier", ""))
        SESSION.role_label   = r.get("label", "")

        # ✅ Restaurer le dernier chapitre actif depuis .role.yaml
        from core import role_manager
        role_data = role_manager.lire_role(SESSION.role_dossier)
        SESSION.chapitre_actif = role_data.get("config", {}).get("dernier_chapitre_actif", "")

        from ui.screens.screen_main_menu import MainMenuScreen

        # ── Rôle Nettoyage : vérifier CBZ en attente ──────────────────────────
        if r.get("dossier") == "01_Clean":
            from core import project_manager
            from ui.screens.screen_cbz_alert import CbzAlertScreen

            cbz_en_attente = project_manager.detecter_cbz_en_attente(
                SESSION.projet_chemin
            )
            if cbz_en_attente:
                self.app.push_screen(CbzAlertScreen())
                return
        # ──────────────────────────────────────────────────────────────────────

        self.app.push_screen(MainMenuScreen())