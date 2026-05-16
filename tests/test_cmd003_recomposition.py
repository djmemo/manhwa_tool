"""
Tests unitaires pour cmd_003_fusion_par_groupe (recomposition).
Testent uniquement les fonctions métier pures, sans UI Textual.
"""
import os
import pytest
from PIL import Image
from commands.cmd_003_fusion_par_groupe import (
    grouper_images,
    recomposer_groupe,
    detecter_conflits,
    executer_recomposition,
    SEPARATEUR,
)


class TestGrouperImages:
    def test_detecte_groupes_et_simples(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        assert set(groupes.keys()) == {"001", "002"}
        assert len(groupes["001"]) == 3
        assert len(groupes["002"]) == 2
        assert len(simples) == 1
        assert simples[0].endswith("003.jpg")

    def test_parties_triees(self, tmp_clean_jpeg):
        groupes, _ = grouper_images(tmp_clean_jpeg["src"])
        # Les parties doivent être dans l'ordre 001, 002, 003
        basenames = [os.path.basename(p) for p in groupes["001"]]
        assert basenames == sorted(basenames)

    def test_dossier_vide(self, tmp_path):
        vide = tmp_path / "vide"
        vide.mkdir()
        groupes, simples = grouper_images(str(vide))
        assert groupes == {}
        assert simples == []

    def test_separateur_correct(self, tmp_clean_jpeg):
        groupes, _ = grouper_images(tmp_clean_jpeg["src"])
        for base, parties in groupes.items():
            for p in parties:
                assert SEPARATEUR in os.path.basename(p)


class TestRecomposerGroupe:
    def test_hauteur_totale(self, tmp_clean_jpeg):
        groupes, _ = grouper_images(tmp_clean_jpeg["src"])
        result = recomposer_groupe(groupes["001"])
        # 3 parties de 300px chacune
        assert result.height == 900
        assert result.width  == 200

    def test_resultat_est_image(self, tmp_clean_jpeg):
        groupes, _ = grouper_images(tmp_clean_jpeg["src"])
        result = recomposer_groupe(groupes["001"])
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_page_deux_parties(self, tmp_clean_jpeg):
        groupes, _ = grouper_images(tmp_clean_jpeg["src"])
        result = recomposer_groupe(groupes["002"])
        assert result.height == 800   # 2 × 400
        assert result.width  == 200


class TestDetecterConflits:
    def test_pas_de_conflit_si_dst_vide(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        conflits = detecter_conflits(groupes, simples, tmp_clean_jpeg["dst"],
                                     jpeg=True, png=False)
        assert conflits == []

    def test_conflit_detecte(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        # Créer un fichier en destination
        open(os.path.join(tmp_clean_jpeg["dst"], "001.jpg"), "w").close()
        conflits = detecter_conflits(groupes, simples, tmp_clean_jpeg["dst"],
                                     jpeg=True, png=False)
        assert "001.jpg" in conflits

    def test_conflit_png(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        open(os.path.join(tmp_clean_jpeg["dst"], "002.png"), "w").close()
        conflits = detecter_conflits(groupes, simples, tmp_clean_jpeg["dst"],
                                     jpeg=False, png=True)
        assert "002.png" in conflits


class TestExecuterRecomposition:
    def test_jpeg_produit_fichiers(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        res = executer_recomposition(
            groupes, simples, tmp_clean_jpeg["dst"],
            quality=90, jpeg=True, png=False)
        assert res["pages_recomposees"] == 2
        assert res["pages_copiees"]     == 1
        assert os.path.isfile(os.path.join(tmp_clean_jpeg["dst"], "001.jpg"))
        assert os.path.isfile(os.path.join(tmp_clean_jpeg["dst"], "002.jpg"))
        assert os.path.isfile(os.path.join(tmp_clean_jpeg["dst"], "003.jpg"))

    def test_png_produit_fichiers(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        res = executer_recomposition(
            groupes, simples, tmp_clean_jpeg["dst"],
            quality=95, jpeg=False, png=True)
        assert os.path.isfile(os.path.join(tmp_clean_jpeg["dst"], "001.png"))
        assert os.path.isfile(os.path.join(tmp_clean_jpeg["dst"], "002.png"))
        assert os.path.isfile(os.path.join(tmp_clean_jpeg["dst"], "003.png"))

    def test_double_format(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        res = executer_recomposition(
            groupes, simples, tmp_clean_jpeg["dst"],
            quality=90, jpeg=True, png=True)
        # 3 pages × 2 formats = 6 fichiers
        assert res["fichiers_ecrits"] == 6

    def test_progress_callback(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        appels = []
        def cb(current, total, msg):
            appels.append((current, total))
        executer_recomposition(
            groupes, simples, tmp_clean_jpeg["dst"],
            quality=90, jpeg=True, png=False, progress_cb=cb)
        # 2 groupes + 1 simple = 3 appels
        assert len(appels) == 3
        # Le dernier appel doit avoir current == total
        assert appels[-1][0] == appels[-1][1]

    def test_image_recomposee_correcte(self, tmp_clean_jpeg):
        groupes, simples = grouper_images(tmp_clean_jpeg["src"])
        executer_recomposition(
            groupes, simples, tmp_clean_jpeg["dst"],
            quality=95, jpeg=True, png=False)
        img = Image.open(os.path.join(tmp_clean_jpeg["dst"], "001.jpg"))
        # 3 parties de 300px chacune
        assert img.height == 900
        assert img.width  == 200
