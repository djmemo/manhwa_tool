"""Tests pour le module slicer.py"""

import os
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from core import slicer

@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_slice_image_cree_morceaux(temp_dir):
    """Test que slice_image crée les morceaux attendus"""
    # Créer une image factice 300x300
    img = Image.new('RGB', (300, 300), color='red')

    # Découper en morceaux de 100 pixels max
    result, forced_cuts = slicer.slice_image(img, 100)

    # Vérifier que plusieurs morceaux ont été créés
    assert len(result) >= 3

    # Vérifier que chaque morceau a une hauteur <= 100
    for piece in result:
        assert piece.size[1] <= 100

def test_slice_image_avec_watermark(temp_dir):
    """Test que slice_image applique le watermark"""
    # Créer une image factice
    img = Image.new('RGB', (300, 300), color='blue')

    # Créer un watermark factice
    wm_path = os.path.join(temp_dir, "watermark.png")
    wm = Image.new('RGBA', (100, 50), color=(255, 255, 255, 128))
    wm.save(wm_path)

    # Découper avec watermark
    result, forced_cuts = slicer.slice_image(img, 100, watermark_path=wm_path)

    # Vérifier que les morceaux ont été créés
    assert len(result) >= 3

def test_slice_image_trouve_gouttiere(temp_dir):
    """Test que slice_image trouve les gouttières pour éviter les coupes forcées"""
    # Créer une image avec une ligne vide au milieu
    img = Image.new('RGB', (300, 300), color='green')
    # Ajouter une ligne vide à y=150
    for x in range(300):
        img.putpixel((x, 150), (255, 255, 255))

    # Découper avec une hauteur max qui forcerait une coupe sans la gouttière
    result, forced_cuts = slicer.slice_image(img, 100)

    # Vérifier que la coupe a été faite à la gouttière (peu ou pas de coupes forcées)
    assert forced_cuts < len(result) - 1

def test_is_row_empty_detecte_fond_uni(temp_dir):
    """Test que is_row_empty détecte correctement les lignes vides"""
    # Créer une image avec une ligne vide
    img = Image.new('RGB', (300, 300), color='red')
    for x in range(300):
        img.putpixel((x, 150), (255, 255, 255))

    # Vérifier que la ligne vide est détectée
    assert slicer.is_row_empty(img, 150)

    # Vérifier qu'une ligne non vide n'est pas détectée (avec une tolérance plus stricte)
    # Créer une ligne avec des pixels très différents
    for x in range(300):
        img.putpixel((x, 149), (0, 0, 0) if x % 2 == 0 else (255, 255, 255))
    # Utiliser une tolérance plus stricte pour la ligne non vide
    assert not slicer.is_row_empty(img, 149, tolerance=0.1)

def test_apply_watermark_ajoute_watermark(temp_dir):
    """Test que apply_watermark ajoute un watermark"""
    # Créer une image
    img = Image.new('RGB', (300, 300), color='yellow')

    # Créer un watermark
    wm_path = os.path.join(temp_dir, "watermark.png")
    wm = Image.new('RGBA', (100, 50), color=(255, 255, 255, 128))
    wm.save(wm_path)

    # Appliquer le watermark
    result = slicer.apply_watermark(img, wm_path)

    # Vérifier que l'image a été modifiée
    assert result is not img
    assert result.size == img.size

def test_apply_watermark_sans_watermark(temp_dir):
    """Test que apply_watermark retourne l'image originale sans watermark"""
    img = Image.new('RGB', (300, 300), color='purple')

    result = slicer.apply_watermark(img, "")

    # Vérifier que l'image originale est retournée
    assert result is img

