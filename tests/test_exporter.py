"""Tests pour le module exporter.py"""

import os
import tempfile
import zipfile
from pathlib import Path

import pytest
from PIL import Image

from core import exporter

@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_exporter_multi_cibles_cree_dossiers(temp_dir):
    """Test que exporter_multi_cibles crée les dossiers nécessaires"""
    # Créer des images factices
    slices = [Image.new('RGB', (100, 100), color='red') for _ in range(3)]

    # Exporter
    result = exporter.exporter_multi_cibles(slices, temp_dir, "test_chapter")

    # Vérifier que les dossiers ont été créés
    assert os.path.exists(os.path.join(temp_dir, "Webtoon_Slices_PNG"))
    assert os.path.exists(os.path.join(temp_dir, "Webtoon_Slices_JPEG"))

    # Vérifier le résultat
    assert result["slices_count"] == 3
    assert result["files_created"] == 7  # 3 PNG + 3 JPEG + 1 CBZ
    assert result["cbz_path"] is not None

def test_exporter_multi_cibles_sans_png(temp_dir):
    """Test que exporter_multi_cibles fonctionne sans PNG"""
    slices = [Image.new('RGB', (100, 100), color='red') for _ in range(2)]

    result = exporter.exporter_multi_cibles(slices, temp_dir, "test", png=False, cbz=True, jpeg=True)
    print(result)
    # Vérifier que seul le dossier JPEG a été créé
    assert not os.path.exists(os.path.join(temp_dir, "Webtoon_Slices_PNG"))
    assert os.path.exists(os.path.join(temp_dir, "Webtoon_Slices_JPEG"))

    # Vérifier le résultat
    assert result["slices_count"] == 2
    assert result["files_created"] == 3  # 2 JPEG seulement + 1 CBZ
    assert result["cbz_path"] is not None

def test_exporter_multi_cibles_sans_jpeg(temp_dir):
    """Test que exporter_multi_cibles fonctionne sans JPEG"""
    slices = [Image.new('RGB', (100, 100), color='red') for _ in range(2)]

    result = exporter.exporter_multi_cibles(slices, temp_dir, "test", png=True, cbz=True, jpeg=False)

    # Vérifier que seul le dossier PNG a été créé
    assert os.path.exists(os.path.join(temp_dir, "Webtoon_Slices_PNG"))
    assert not os.path.exists(os.path.join(temp_dir, "Webtoon_Slices_JPEG"))

    # Vérifier le résultat
    assert result["slices_count"] == 2
    assert result["files_created"] == 3  # 2 PNG seulement + 1 CBZ
    assert result["cbz_path"] is not None

def test_exporter_multi_cibles_sans_cbz(temp_dir):
    """Test que exporter_multi_cibles fonctionne sans CBZ"""
    slices = [Image.new('RGB', (100, 100), color='red') for _ in range(2)]

    result = exporter.exporter_multi_cibles(slices, temp_dir, "test", cbz=False)

    # Vérifier que le CBZ n'a pas été créé
    assert result["cbz_path"] is None

    # Vérifier le résultat
    assert result["slices_count"] == 2
    assert result["files_created"] == 4  # 2 PNG + 2 JPEG

def test_exporter_multi_cibles_cree_fichiers_corrects(temp_dir):
    """Test que exporter_multi_cibles crée les fichiers avec les bons noms"""
    slices = [Image.new('RGB', (100, 100), color='red') for _ in range(3)]

    result = exporter.exporter_multi_cibles(slices, temp_dir, "test_chapter")

    # Vérifier les fichiers PNG
    png_dir = os.path.join(temp_dir, "Webtoon_Slices_PNG")
    png_files = sorted(os.listdir(png_dir))
    assert png_files == ["001.png", "002.png", "003.png"]

    # Vérifier les fichiers JPEG
    jpeg_dir = os.path.join(temp_dir, "Webtoon_Slices_JPEG")
    jpeg_files = sorted(os.listdir(jpeg_dir))
    assert jpeg_files == ["001.jpg", "002.jpg", "003.jpg"]

    # Vérifier le CBZ
    assert result["cbz_path"].endswith("_Release.cbz")
    with zipfile.ZipFile(result["cbz_path"], 'r') as zf:
        cbz_files = sorted(zf.namelist())
        assert cbz_files == ["001.jpg", "002.jpg", "003.jpg"]
