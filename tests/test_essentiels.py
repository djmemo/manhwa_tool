"""
Tests unitaires essentiels pour l'application.
"""
import os
import pytest
import tempfile
from core import project_manager, role_manager, status_manager, archive_manager

def test_creer_projet_valide():
    """Tester la création de projet avec chemin valide"""
    with tempfile.TemporaryDirectory() as tmpdir:
        projet_path = project_manager.creer_projet(tmpdir, "TestProjet")
        assert os.path.exists(projet_path)
        assert os.path.isdir(projet_path)

def test_creer_role_valide():
    """Tester la création de rôle avec chemin valide"""
    with tempfile.TemporaryDirectory() as tmpdir:
        role_path = role_manager.creer_role(tmpdir, "TestRole", "TestRole")
        assert os.path.exists(role_path)
        assert os.path.isdir(role_path)

def test_creer_status_valide():
    """Tester la création de statut avec chemin valide"""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_data = status_manager.creer_status(tmpdir, "Chapter 01", "Cleaner")
        status_file = os.path.join(tmpdir, ".status.yaml")
        assert os.path.exists(status_file)
        assert os.path.isfile(status_file)

def test_archiver_chapitre_valide():
    """Tester l'archivage de chapitre avec chemins valides"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer une structure de base
        projet_path = project_manager.creer_projet(tmpdir, "TestProjet")
        role_path = role_manager.creer_role(projet_path, "01_Clean", "01_Clean")
        chapter_path = os.path.join(role_path, "Chapter 01")
        os.makedirs(chapter_path)
        status_path = status_manager.creer_status(chapter_path, "Chapter 01", "Cleaner")

        # Marquer toutes les étapes comme terminées
        for etape in ["extraction_cbz", "upscale", "nettoyage_psd", "export_jpeg", "fusion_finale"]:
            status_manager.marquer_etape(chapter_path, etape, "0:00:01")

        # Tester l'archivage
        archive_path = archive_manager.archiver_chapitre(chapter_path, tmpdir)
        assert os.path.exists(archive_path)
        assert os.path.isfile(archive_path)

def test_passer_en_archive_valide():
    """Tester le passage en archive avec chemin valide"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier .status.yaml pour simuler un chapitre existant
        status_manager.creer_status(tmpdir, "Chapter 01", "Cleaner")
        status_manager.marquer_etape(tmpdir, "extraction_cbz", "0:01:00")
        status_manager.marquer_etape(tmpdir, "upscale", "0:02:00")
        status_manager.marquer_etape(tmpdir, "nettoyage_psd", "0:03:00")
        status_manager.marquer_etape(tmpdir, "export_jpeg", "0:04:00")
        status_manager.marquer_etape(tmpdir, "fusion_finale", "0:05:00")
        # Créer une image dans le dossier pour simuler un chapitre complet
        with open(os.path.join(tmpdir, "page1.jpg"), "w") as f:
            f.write("fake image data")
        # Vérifier le statut avant l'archivage
        statut_before = status_manager.lire_status(tmpdir)
        print(f"Statut avant archivage: {statut_before['statut_global']}")
        archive_manager.passer_en_archive(tmpdir)
        # Vérifier que le statut a été mis à jour
        statut = status_manager.lire_status(tmpdir)
        print(f"Statut après archivage: {statut['statut_global']}")
        assert statut["statut_global"] == "archive"

def test_lire_status_valide():
    """Tester la lecture de statut avec fichier valide"""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_path = status_manager.creer_status(tmpdir, "Chapter 01", "Cleaner")
        statut = status_manager.lire_status(tmpdir)
        assert statut is not None
        assert "statut_global" in statut

def test_marquer_etape_valide():
    """Tester le marquage d'étape avec temps valide"""
    with tempfile.TemporaryDirectory() as tmpdir:
        status_manager.creer_status(tmpdir, "Chapter 01", "Cleaner")
        status_manager.marquer_etape(tmpdir, "extraction_cbz", "0:05:00")
        statut = status_manager.lire_status(tmpdir)
        assert "etapes" in statut
        assert "extraction_cbz" in statut["etapes"]
        assert statut["etapes"]["extraction_cbz"]["duree"] == "0:05:00"

def test_est_archivable_valide():
    """Tester la vérification d'archivage avec statut valide"""
    statut_complet = {
        "statut_global": "termine",
        "extraction_cbz": {"temps": "0:01:00", "statut": "terminé"},
        "upscale": {"temps": "0:02:00", "statut": "terminé"},
        "nettoyage_psd": {"temps": "0:03:00", "statut": "terminé"},
        "export_jpeg": {"temps": "0:04:00", "statut": "terminé"},
        "fusion_finale": {"temps": "0:05:00", "statut": "terminé"}
    }
    assert archive_manager.est_archivable(statut_complet) is True

def test_est_archivable_incomplet():
    """Tester la vérification d'archivage avec statut incomplet"""
    statut_incomplet = {
        "statut_global": "en_cours",
        "extraction_cbz": {"temps": "0:01:00", "statut": "terminé"},
        "upscale": {"temps": "0:02:00", "statut": "terminé"},
        "nettoyage_psd": {"temps": "0:03:00", "statut": "en_cours"},
        "export_jpeg": {"temps": "0:04:00", "statut": "terminé"},
        "fusion_finale": {"temps": "0:05:00", "statut": "terminé"}
    }
    assert archive_manager.est_archivable(statut_incomplet) is False
