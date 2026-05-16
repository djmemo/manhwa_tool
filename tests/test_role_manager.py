import os, pytest
from core import project_manager, role_manager
from session import SESSION

@pytest.fixture
def role_setup(tmp_project):
    pj = project_manager.creer_projet(tmp_project["racine"], "R")
    SESSION.projet_chemin = pj
    SESSION.role_dossier = os.path.join(pj, "01_Clean")
    role_manager.creer_role(pj, "01_Clean", "Cleaner")
    return pj

def test_creer_et_lire_role(role_setup):
    data = role_manager.lire_role(SESSION.role_dossier)
    assert data["role"]["label"] == "Cleaner"

def test_lister_roles(role_setup):
    roles = role_manager.lister_roles(role_setup)
    assert len(roles) == 1
    assert roles[0]["label"] == "Cleaner"

def test_init_sous_dossiers(role_setup):
    role_manager.init_sous_dossiers(SESSION.role_dossier, "Chapter 01")
    assert os.path.isdir(os.path.join(SESSION.role_dossier, "Chapter 01", "01_Original_RAW"))

def test_sauvegarder_role_securite(role_setup):
    autre = os.path.join(role_setup, "02_Translation")
    os.makedirs(autre, exist_ok=True)
    with pytest.raises(ValueError):
        role_manager.sauvegarder_role(autre, {})

def test_mettre_a_jour_champ(role_setup):
    role_manager.mettre_a_jour_champ(SESSION.role_dossier, "config.model_esrgan", "test_model")
    data = role_manager.lire_role(SESSION.role_dossier)
    assert data["config"]["model_esrgan"] == "test_model"
