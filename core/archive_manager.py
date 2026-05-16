import os, zipfile
from datetime import datetime

def est_archivable(status: dict) -> bool:
    return status.get("statut_global") == "termine"

def archiver_chapitre(chapitre_chemin: str, destination: str) -> str:
    os.makedirs(destination, exist_ok=True)
    nom_zip = f"archive_{os.path.basename(chapitre_chemin)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(destination, nom_zip)
    merged_dir = os.path.join(chapitre_chemin, "04_Final_Merged")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(merged_dir):
            for f in os.listdir(merged_dir):
                zf.write(os.path.join(merged_dir, f), f)
        st_file = os.path.join(chapitre_chemin, ".status.yaml")
        if os.path.exists(st_file): zf.write(st_file, ".status.yaml")
    return zip_path

def passer_en_archive(chapitre_chemin: str):
    from core.status_manager import passer_a_statut
    passer_a_statut(chapitre_chemin, "archive")
