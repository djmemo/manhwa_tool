import pytest
from core import project_manager, changelog

def test_ajouter_entree_et_lire(tmp_project):
    pj = project_manager.creer_projet(tmp_project["racine"], "CL")
    changelog.ajouter_entree(pj, "Cleaner", "Action test")
    entries = changelog.lire_changelog(pj)
    assert len(entries) == 1
    assert entries[0]["action"] == "Action test"

def test_append_only(tmp_project):
    pj = project_manager.creer_projet(tmp_project["racine"], "AO")
    for i in range(3): changelog.ajouter_entree(pj, "R", f"action {i}")
    before = len(changelog.lire_changelog(pj, limit=100))
    changelog.ajouter_entree(pj, "R", "encore")
    after = len(changelog.lire_changelog(pj, limit=100))
    assert after == before + 1

def test_lire_limit(tmp_project):
    pj = project_manager.creer_projet(tmp_project["racine"], "LM")
    for i in range(10): changelog.ajouter_entree(pj, "R", f"a{i}")
    entries = changelog.lire_changelog(pj, limit=3)
    assert len(entries) == 3

def test_chemin_invalide():
    changelog.ajouter_entree("/chemin/invalide", "R", "action")
    assert changelog.lire_changelog("/chemin/invalide") == []
