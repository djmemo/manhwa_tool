import os
from textual.widgets import DataTable
from core import status_manager, role_manager
class StatusTable(DataTable):
    def populate(self, projet_chemin: str):
        self.clear(columns=True)
        self.add_columns("Chapitre","Extraction","Upscale","Nettoyage","Export","Fusion","Global")
        for role in role_manager.lister_roles(projet_chemin):
            rc = os.path.join(projet_chemin, role.get("dossier",""))
            if not os.path.isdir(rc): continue
            for ch in sorted(os.listdir(rc)):
                cc = os.path.join(rc, ch)
                if not os.path.isfile(os.path.join(cc, ".status.yaml")): continue
                st = status_manager.lire_status(cc)
                e = st.get("etapes", {})
                cell = lambda k: "✔" if e.get(k,{}).get("done") else "–"
                self.add_row(ch,cell("extraction_cbz"),cell("upscale"),cell("nettoyage_psd"),cell("export_jpeg"),cell("fusion_finale"),st.get("statut_global","?"))
