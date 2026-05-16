"""
screen_pipeline.py — Écran dédié au pipeline complet.
Affiche la liste des étapes avec leur statut en temps réel.
"""
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Footer, ListView, ListItem
from textual.binding import Binding
from textual.reactive import reactive
from ui.widgets.breadcrumb import Breadcrumb

# Statuts visuels
ICONES = {
    "attente":  "⏳",
    "en_cours": "🔄",
    "ok":       "✅",
    "ignore":   "⏭",
    "erreur":   "❌",
    "manuel":   "👋",
}


class PipelineScreen(Screen):
    """
    Écran affiché pendant l'exécution du pipeline.
    Chaque étape est une ligne mise à jour en temps réel.
    """
    BINDINGS = [Binding("escape", "fermer", "Fermer", show=False)]

    def __init__(self, etapes: list[tuple[str, str]]):
        """
        etapes : liste de (cle, label_affiche)
        ex: [("extraction_cbz", "Extraction CBZ"), ("upscale", "Upscale Real-ESRGAN"), ...]
        """
        super().__init__()
        self._etapes = etapes                      # [(cle, label), ...]
        self._statuts: dict[str, str] = {k: "attente" for k, _ in etapes}
        self._details: dict[str, str] = {k: ""      for k, _ in etapes}
        self._items:   dict[str, ListItem] = {}

    def compose(self) -> ComposeResult:
        yield Breadcrumb(id="breadcrumb")
        yield Label("⚙️  Pipeline en cours…", id="lbl_titre", classes="title")
        yield ListView(id="lv_etapes")
        yield Footer()

    def on_mount(self) -> None:
        lv = self.query_one("#lv_etapes", ListView)
        for cle, label in self._etapes:
            item = ListItem(Label(self._render_ligne(cle, label), id=f"lbl_{cle}"))
            item._cle = cle
            self._items[cle] = item
            lv.append(item)

    def _render_ligne(self, cle: str, label: str) -> str:
        icone  = ICONES.get(self._statuts.get(cle, "attente"), "⏳")
        detail = self._details.get(cle, "")
        suffix = f"  [{detail}]" if detail else ""
        return f"{icone}  {label}{suffix}"

    def mettre_a_jour(self, cle: str, statut: str, detail: str = "") -> None:
        """Appelé depuis le worker via app.call_from_thread()."""
        self._statuts[cle] = statut
        self._details[cle] = detail
        label_affiche = next((l for k, l in self._etapes if k == cle), cle)
        try:
            self.query_one(f"#lbl_{cle}", Label).update(
                self._render_ligne(cle, label_affiche))
        except Exception:
            pass

    def terminer(self, message: str = "✅ Pipeline terminé") -> None:
        """Met à jour le titre de l'écran à la fin du pipeline."""
        try:
            self.query_one("#lbl_titre", Label).update(message)
        except Exception:
            pass

    def action_fermer(self) -> None:
        self.app.pop_screen()
