"""
cmd_000 — Sélection d'un chapitre existant
-------------------------------------------
Affiche la liste des chapitres déjà initialisés dans le rôle actif,
avec leur statut (en_cours / termine / en_attente).
Sélectionner un chapitre met à jour SESSION.chapitre_actif pour
toutes les commandes suivantes.
"""
import os
from textual.screen import ModalScreen
from textual.app import ComposeResult
from textual.widgets import Label, Button, ListView, ListItem
from textual.containers import Vertical, Horizontal

LABEL = "Sélectionner un chapitre"
DESCRIPTION = 'Reprend ou commence un chapitre existant dans le rôle actif'
class SelectChapitreModal(ModalScreen[str]):
    DEFAULT_CSS = '''
    SelectChapitreModal { align: center middle; }
    #dialog {
        padding: 1 2;
        background: #1a1a2e;
        border: solid #4a4e69;
        width: 55;
        height: auto;
        max-height: 80vh;
    }
    #lbl_title  { margin-bottom: 1; }
    #lbl_actif  { color: #a8dadc; margin-bottom: 1; }
    ListView    { height: auto; max-height: 20; margin-bottom: 1; }
    #btn_cancel { margin-top: 1; }
    '''

    def __init__(self, chapitres: list[tuple[str, str]], actif: str):
        super().__init__()
        self._chapitres = chapitres   # [(nom, statut_global), ...]
        self._actif = actif

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("📂 Sélectionner un chapitre", id="lbl_title", classes="title")
            if self._actif:
                yield Label(f"Actif : {self._actif}", id="lbl_actif")
            self._lv = ListView(id="lv_chapitres")
            yield self._lv
            yield Button("Annuler", id="btn_cancel", variant="default")

    def on_mount(self):
        ICONS = {"termine": "✅", "en_cours": "🔄", "en_attente": "⏳"}
        for nom, statut in self._chapitres:
            icone = ICONS.get(statut, "📁")
            item = ListItem(Label(f"{icone} {nom}  [{statut}]"))
            item._chapitre_nom = nom
            self._lv.append(item)

    def on_list_view_selected(self, event: ListView.Selected):
        self.dismiss(event.item._chapitre_nom)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_cancel":
            self.dismiss(None)


def _lister_chapitres(role_dossier: str) -> list[tuple[str, str]]:
    """Retourne [(nom_chapitre, statut_global)] triés, en lisant chaque .status.yaml."""
    from core.utils import lire_yaml
    result = []
    if not os.path.isdir(role_dossier):
        return result
    for entry in sorted(os.listdir(role_dossier)):
        chap_chemin = os.path.join(role_dossier, entry)
        status_file = os.path.join(chap_chemin, ".status.yaml")
        if os.path.isdir(chap_chemin) and os.path.isfile(status_file):
            data = lire_yaml(status_file)
            statut = data.get("statut_global", "en_cours") if isinstance(data, dict) else "en_cours"
            result.append((entry, statut))
    return result


def run(app=None) -> None:
    if not app:
        return

    from session import SESSION
    from ui.notify import notify_warn, notify_ok

    chapitres = _lister_chapitres(SESSION.role_dossier)

    if not chapitres:
        notify_warn(app, "Aucun chapitre existant dans ce rôle.\nUtilisez 'Créer un chapitre' d'abord.")
        return

    def on_selected(nom: str | None) -> None:
        if not nom:
            return
        SESSION.chapitre_actif = nom
        # Rafraîchir le fil d'Ariane sur tous les écrans empilés
        for screen in app.screen_stack:
            try:
                screen.query_one("Breadcrumb").refresh_breadcrumb()
            except Exception:
                pass
        notify_ok(app, f"Chapitre actif : {nom}")

    app.push_screen(
        SelectChapitreModal(chapitres, actif=SESSION.chapitre_actif),
        on_selected,
    )
