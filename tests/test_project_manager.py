import os, pytest
from core import project_manager

def test_creer_et_lire_projet(tmp_project):
    chemin = project_manager.creer_projet(tmp_project["racine"], "MonProjet")
    assert os.path.isdir(chemin)
    data = project_manager.lire_projet(chemin)
    assert data["project"]["name"] == "MonProjet"

def test_scan_projets(tmp_project):
    project_manager.creer_projet(tmp_project["racine"], "Proj1")
    project_manager.creer_projet(tmp_project["racine"], "Proj2")
    projets = project_manager.scan_projets(tmp_project["racine"])
    assert len(projets) == 2
    assert project_manager.scan_projets("/chemin/invalide/123") == []

def test_mettre_a_jour_progression_et_prochain(tmp_project):
    chemin = project_manager.creer_projet(tmp_project["racine"], "P")
    assert project_manager.prochain_chapitre(chemin) == 1
    project_manager.mettre_a_jour_progression(chemin, 5)
    assert project_manager.prochain_chapitre(chemin) == 6

def test_detecter_cbz(tmp_project, tmp_cbz):
    import shutil
    shutil.copy(tmp_cbz, os.path.join(tmp_project["projet"], "00_Raw", "ch01.cbz"))
    cbz = project_manager.detecter_cbz_en_attente(tmp_project["projet"])
    assert "ch01.cbz" in cbz

    # Test dossier vide/inexistant
    import shutil
    shutil.rmtree(os.path.join(tmp_project["projet"], "00_Raw"))
    assert project_manager.detecter_cbz_en_attente(tmp_project["projet"]) == []

def test_recalculer_stats(tmp_project):
    from core import status_manager, role_manager
    pj = project_manager.creer_projet(tmp_project["racine"], "S")
    role_manager.creer_role(pj, "01_Clean", "Cleaner")
    role_manager.init_sous_dossiers(os.path.join(pj, "01_Clean"), "Chapter 01")
    ch_chemin = os.path.join(pj, "01_Clean", "Chapter 01")
    status_manager.creer_status(ch_chemin, "Chapter 01", "Cleaner")

    stats = project_manager.recalculer_stats(pj)
    assert stats["chapitres_en_cours"] == 1
    assert stats["chapitres_termines"] == 0
