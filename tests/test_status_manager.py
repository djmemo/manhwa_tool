import os, pytest
from core import project_manager, role_manager, status_manager
from session import SESSION

@pytest.fixture
def chapitre_setup(tmp_project):
    pj = project_manager.creer_projet(tmp_project["racine"], "ST")
    SESSION.role_dossier = os.path.join(pj, "01_Clean")
    role_manager.creer_role(pj, "01_Clean", "Cleaner")
    role_manager.init_sous_dossiers(SESSION.role_dossier, "Chapter 01")
    ch_chemin = os.path.join(SESSION.role_dossier, "Chapter 01")
    status_manager.creer_status(ch_chemin, "Chapter 01", "Cleaner")
    return ch_chemin

def test_creer_et_lire_status(chapitre_setup):
    st = status_manager.lire_status(chapitre_setup)
    assert st["statut_global"] == "en_cours"
    assert "extraction_cbz" in st["etapes"]

def test_marquer_etape_et_terminer(chapitre_setup):
    status_manager.marquer_etape(chapitre_setup, "extraction_cbz", "0:00:05")
    st = status_manager.lire_status(chapitre_setup)
    assert st["etapes"]["extraction_cbz"]["done"] is True
    assert status_manager.est_chapitre_termine(st) is False

    # Marquer toutes les étapes
    for etape in ["upscale", "nettoyage_psd", "export_jpeg", "fusion_finale"]:
        status_manager.marquer_etape(chapitre_setup, etape, "0:00:01")
    st = status_manager.lire_status(chapitre_setup)
    assert status_manager.est_chapitre_termine(st) is True
    assert st["statut_global"] == "termine"

def test_calculer_progression(chapitre_setup):
    st = status_manager.lire_status(chapitre_setup)
    assert status_manager.calculer_progression(st) == 0.0
    status_manager.marquer_etape(chapitre_setup, "extraction_cbz", "0:00:05")
    st = status_manager.lire_status(chapitre_setup)
    assert status_manager.calculer_progression(st) == 0.2

def test_mettre_a_jour_notes(chapitre_setup):
    status_manager.mettre_a_jour_notes(chapitre_setup, "Super note")
    st = status_manager.lire_status(chapitre_setup)
    assert "Super note" in st["notes"]

def test_mettre_a_jour_integrite(chapitre_setup):
    status_manager.mettre_a_jour_integrite(chapitre_setup, 10, 10, True)
    st = status_manager.lire_status(chapitre_setup)
    assert st["integrite"]["verified"] is True
    assert st["integrite"]["raw_count"] == 10

def test_passer_a_statut(chapitre_setup):
    status_manager.passer_a_statut(chapitre_setup, "archive")
    st = status_manager.lire_status(chapitre_setup)
    assert st["statut_global"] == "archive"
