import os, zipfile
from datetime import datetime
from core.utils import validate_path

def est_archivable(status: dict) -> bool:
    return status.get("statut_global") == "termine"

def archiver_chapitre(chapitre_chemin: str, destination: str) -> str:
    if not validate_path(destination):
        raise ValueError(f"Chemin de destination invalide: {destination}")
    os.makedirs(destination, exist_ok=True)
    nom_zip = f"archive_{os.path.basename(chapitre_chemin)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(destination, nom_zip)
    merged_dir = os.path.join(chapitre_chemin, "05_Final_Merged")
    st_file = os.path.join(chapitre_chemin, ".status.yaml")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(merged_dir):
            for f in os.listdir(merged_dir):
                file_path = os.path.join(merged_dir, f)
                if os.path.isfile(file_path):
                    zf.write(file_path, os.path.join("05_Final_Merged", f))
        if os.path.exists(st_file):
            zf.write(st_file, ".status.yaml")
    return zip_path

def passer_en_archive(chapitre_chemin: str) -> None:
    """Passe un chapitre en statut 'archive'."""
    from core.status_manager import passer_a_statut, lire_status

    if not os.path.exists(chapitre_chemin):
        return

    # Vérifier que le statut actuel est "termine" avant de passer en archive
    status = lire_status(chapitre_chemin)
    if status.get("statut_global") != "termine":
        print(f"Chapitre {chapitre_chemin} n'est pas en statut 'termine', statut actuel: {status.get('statut_global')}")
        return

    # Vérifier la présence d'images dans différents emplacements
    if a_des_images(chapitre_chemin):
        passer_a_statut(chapitre_chemin, "archive")
    else:
        print(f"Chapitre {chapitre_chemin} n'a pas d'images, impossible de passer en archive")

def a_des_images(dossier: str) -> bool:
    """Vérifie si un dossier ou ses sous-dossiers contiennent des images."""
    from core.utils import EXTS_IMAGE

    # Vérifier d'abord dans le dossier principal
    if any(f.lower().endswith(EXTS_IMAGE) for f in os.listdir(dossier)):
        return True

    # Vérifier dans 05_Final_Merged
    merged_dir = os.path.join(dossier, "05_Final_Merged")
    if os.path.exists(merged_dir):
        if any(f.lower().endswith(EXTS_IMAGE) for f in os.listdir(merged_dir)):
            return True

    # Vérifier récursivement dans tous les sous-dossiers
    for root, dirs, files in os.walk(dossier):
        for f in files:
            if f.lower().endswith(EXTS_IMAGE):
                return True

    return False
