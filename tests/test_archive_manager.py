import os, pytest
from core import project_manager, role_manager, status_manager, archive_manager
from session import SESSION

@pytest.fixture
def termine_setup(tmp_project):
    pj = project_manager.creer_projet(tmp_project["racine"], "AR")
    SESSION.role_dossier = os.path.join(pj, "01_Clean")
    role_manager.creer_role(pj, "01_Clean", "Cleaner")
    role_manager.init_sous_dossiers(SESSION.role_dossier, "Chapter 01")
    ch_chemin = os.path.join(SESSION.role_dossier, "Chapter 01")
    status_manager.creer_status(ch_chemin, "Chapter 01", "Cleaner")
    for etape in ["extraction_cbz","upscale","nettoyage_psd","export_jpeg","fusion_finale"]:
        status_manager.marquer_etape(ch_chemin, etape, "0:00:01")
    return pj, ch_chemin

def test_est_archivable_true(termine_setup):
    _, ch = termine_setup
    st = status_manager.lire_status(ch)
    assert archive_manager.est_archivable(st) is True

def test_est_archivable_false():
    assert archive_manager.est_archivable({"statut_global": "en_cours"}) is False

def test_archiver_cree_zip_et_passe_archive(termine_setup, tmp_path):
    _, ch = termine_setup
    dest = str(tmp_path / "archives")
    zip_path = archive_manager.archiver_chapitre(ch, dest)
    assert os.path.isfile(zip_path)

    # Créer des images dans 05_Final_Merged pour que passer_en_archive fonctionne
    merged_dir = os.path.join(ch, "05_Final_Merged")
    os.makedirs(merged_dir, exist_ok=True)
    for i in range(3):
        img_path = os.path.join(merged_dir, f"page_{i:03d}.jpg")
        from PIL import Image
        img = Image.new("RGB", (100, 200), color=(i * 50, 0, 0))
        img.save(img_path)

    archive_manager.passer_en_archive(ch)
    st = status_manager.lire_status(ch)
    assert st["statut_global"] == "archive"
