"""
cmd_009 — Notes chapitre
-------------------------
Affiche les notes existantes de chaque chapitre (lues depuis .status.yaml).
Permet d'ajouter une note en mode append (les notes existantes sont
préservées — jamais écrasées).
"""
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, TextArea, ListView, ListItem
from textual.containers import Horizontal, Vertical

LABEL = "Notes Chapitre"
DESCRIPTION = 'Consulter et ajouter des notes sur les chapitres du rôle actif'
def run(app=None):
    if not app: return

    from session import SESSION
    from core import status_manager
    from ui.widgets.breadcrumb import Breadcrumb

    class NotesScreen(Screen):
        DEFAULT_CSS = '''
        #main_container { height: 100%; }
        #left_panel { width: 30%; height: 100%; border-right: solid #00b4d8; }
        #right_panel { width: 70%; height: 100%; padding: 1; }
        #notes_area { height: 1fr; margin-bottom: 1; }
        #input_container { height: auto; }
        '''

        def compose(self) -> ComposeResult:
            yield Breadcrumb(id="breadcrumb")

            with Horizontal(id="main_container"):
                # Panneau gauche : liste des chapitres
                with Vertical(id="left_panel"):
                    yield Label("Chapitres", classes="title")
                    self.lv = ListView()
                    yield self.lv
                    yield Button("Retour", id="btn_back", variant="error")

                # Panneau droit : affichage/ajout des notes
                with Vertical(id="right_panel"):
                    self.lbl_current = Label("Sélectionnez un chapitre à gauche", classes="title")
                    yield self.lbl_current

                    self.notes_area = TextArea(read_only=True, id="notes_area")
                    yield self.notes_area

                    with Horizontal(id="input_container"):
                        self.inp_note = Input(placeholder="Ajouter une note pour ce chapitre...", id="inp_note")
                        yield self.inp_note
                        yield Button("Ajouter", id="btn_add", variant="primary")

        def on_mount(self):
            import os
            # On peuple la liste des chapitres
            if not SESSION.role_dossier: return

            for ch in sorted(os.listdir(SESSION.role_dossier)):
                ch_path = os.path.join(SESSION.role_dossier, ch)
                if os.path.isfile(os.path.join(ch_path, ".status.yaml")):
                    self.lv.append(ListItem(Label(ch)))

            self._chapitre_selectionne = None

        def on_list_view_selected(self, event: ListView.Selected):
            import os
            nom_ch = str(event.item.query_one(Label).render())
            self._chapitre_selectionne = os.path.join(SESSION.role_dossier, nom_ch)

            self.lbl_current.update(f"📝 Notes : {nom_ch}")
            self._rafraichir_notes()

        def _rafraichir_notes(self):
            if not self._chapitre_selectionne: return
            st = status_manager.lire_status(self._chapitre_selectionne)
            self.notes_area.text = st.get("notes", "Aucune note pour le moment.")

        def on_button_pressed(self, event: Button.Pressed):
            if event.button.id == "btn_back":
                self.app.pop_screen()
            elif event.button.id == "btn_add":
                if not self._chapitre_selectionne:
                    from ui.notify import notify_warn
                    notify_warn(self.app, "Veuillez d'abord sélectionner un chapitre.")
                    return

                texte = self.inp_note.value.strip()
                if texte:
                    status_manager.mettre_a_jour_notes(self._chapitre_selectionne, texte)
                    self.inp_note.value = ""
                    self._rafraichir_notes()
                    from ui.notify import notify_ok
                    notify_ok(self.app, "Note ajoutée.")

    app.push_screen(NotesScreen())
