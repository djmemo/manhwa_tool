"""
tests/test_cmd_010_auto_pipeline.py — Tests unitaires du pipeline automatique.
Valide: extraction numéro, PipelineProgress, affichage.
"""
import os
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import les fonctions à tester
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commands.cmd_010_surveiller_raw import (
    extract_chapter_number,
    chapter_exists,
    PipelineProgress,
)


class TestExtractChapterNumber(unittest.TestCase):
    """Tests: extraction du numéro de chapitre depuis le nom du CBZ."""

    def test_format_chapitre_nn(self):
        """Format: *_chapitre_42* → 42"""
        self.assertEqual(extract_chapter_number("manga_chapitre_42.cbz"), 42)
        self.assertEqual(extract_chapter_number("chapitre_06.cbz"), 6)
        self.assertEqual(extract_chapter_number("chapitre_001.zip"), 1)

    def test_format_nn_underscore(self):
        """Format: NN_* → NN"""
        self.assertEqual(extract_chapter_number("42_raw.cbz"), 42)
        self.assertEqual(extract_chapter_number("06_images.zip"), 6)

    def test_case_insensitive(self):
        """Format insensible à la casse."""
        self.assertEqual(extract_chapter_number("CHAPITRE_42.cbz"), 42)
        self.assertEqual(extract_chapter_number("Chapitre_06.zip"), 6)
        self.assertEqual(extract_chapter_number("Chapter 71_4dc41b.cbz"), 71)

    def test_invalid_no_number(self):
        """Format invalide: pas de numéro détecté → None"""
        self.assertIsNone(extract_chapter_number("invalid.cbz"))
        self.assertIsNone(extract_chapter_number("raw_images.zip"))

    def test_edge_cases(self):
        """Cas limites."""
        self.assertEqual(extract_chapter_number("chapitre_0.cbz"), 0)
        self.assertEqual(extract_chapter_number("999_final.cbz"), 999)


class TestPipelineProgress(unittest.TestCase):
    """Tests: suivi de la progression du pipeline."""

    def setUp(self):
        self.progress = PipelineProgress()

    def test_initial_state(self):
        """État initial: tout en attente."""
        self.assertEqual(self.progress.steps["creation_chapitre"]["status"], "pending")
        self.assertEqual(self.progress.steps["extraction_images"]["status"], "pending")
        self.assertFalse(self.progress.is_success())

    def test_step_lifecycle(self):
        """Cycle de vie d'une étape: pending → running → done."""
        self.progress.start_step("creation_chapitre")
        self.assertEqual(self.progress.steps["creation_chapitre"]["status"], "running")

        self.progress.finish_step("creation_chapitre", message="Chapter 42 créé")
        self.assertEqual(self.progress.steps["creation_chapitre"]["status"], "done")
        self.assertEqual(self.progress.steps["creation_chapitre"]["message"], "Chapter 42 créé")

    def test_error_handling(self):
        """Gestion des erreurs : status = "error", error message stocké."""
        self.progress.start_step("extraction_images")
        self.progress.finish_step("extraction_images", error="Archive vide")
        self.assertEqual(self.progress.steps["extraction_images"]["status"], "error")
        self.assertEqual(self.progress.steps["extraction_images"]["error"], "Archive vide")

    def test_duration_calculation(self):
        """Calcul de la durée d'une étape."""
        import time
        self.progress.start_step("creation_chapitre")
        time.sleep(0.1)  # Simuler un peu de temps
        self.progress.finish_step("creation_chapitre", message="OK")
        
        duration = self.progress.get_duration("creation_chapitre")
        self.assertNotEqual(duration, "—")
        # Durée > 0.1s
        self.assertTrue(duration.startswith("0:"))

    def test_success_detection(self):
        """Détection du succès: toutes les étapes = "done"."""
        self.assertFalse(self.progress.is_success())
        
        self.progress.finish_step("creation_chapitre", message="OK")
        self.assertFalse(self.progress.is_success())  # Pas toutes les étapes
        
        self.progress.finish_step("extraction_images", message="OK")
        self.assertTrue(self.progress.is_success())  # Toutes les étapes done

    def test_chapter_metadata(self):
        """Stockage des métadonnées du chapitre."""
        self.progress.chapter_name = "Chapter 42"
        self.progress.chapter_path = "/path/to/Chapter 42"
        self.progress.extracted_count = 142
        
        self.assertEqual(self.progress.chapter_name, "Chapter 42")
        self.assertEqual(self.progress.extracted_count, 142)


class TestChapterExists(unittest.TestCase):
    """Tests: vérification de l'existence d'un chapitre."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_chapter_exists(self):
        """Le chapitre existe."""
        chapter_path = os.path.join(self.temp_dir, "Chapter 42")
        os.makedirs(chapter_path)
        
        self.assertTrue(chapter_exists(self.temp_dir, 42))

    def test_chapter_not_exists(self):
        """Le chapitre n'existe pas."""
        self.assertFalse(chapter_exists(self.temp_dir, 42))

    def test_chapter_formatting(self):
        """Vérifier la formation du nom: Chapter XX (avec zéro-padding)."""
        chapter_path = os.path.join(self.temp_dir, "Chapter 06")
        os.makedirs(chapter_path)
        
        self.assertTrue(chapter_exists(self.temp_dir, 6))  # "Chapter 06"
        self.assertFalse(chapter_exists(self.temp_dir, 7))
