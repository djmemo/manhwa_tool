import os, pytest
from PIL import Image
from core import integrity_checker

def test_compter_images(tmp_path):
    assert integrity_checker.compter_images("/chemin/invalide", [".jpg"]) == 0
    for i in range(3):
        Image.new("RGB", (10,10)).save(str(tmp_path / f"img_{i}.jpg"))
    assert integrity_checker.compter_images(str(tmp_path), [".jpg"]) == 3

def test_verifier_egalite_et_rapport(tmp_path):
    src = tmp_path / "src"; dst = tmp_path / "dst"
    src.mkdir(); dst.mkdir()
    for i in range(3):
        Image.new("RGB", (10,10)).save(str(src / f"p{i}.jpg"))
        Image.new("RGB", (10,10)).save(str(dst / f"p{i}.jpg"))

    result = integrity_checker.verifier(str(src), str(dst), [".jpg"])
    assert result["verified"] is True

    rapport = integrity_checker.rapport_integrite(str(src), str(dst))
    assert rapport["verified"] is True
    assert rapport["raw_count"] == 3

def test_detecte_manquants(tmp_path):
    src = tmp_path / "s"; dst = tmp_path / "d"
    src.mkdir(); dst.mkdir()
    Image.new("RGB",(10,10)).save(str(src/"a.jpg"))
    result = integrity_checker.verifier(str(src), str(dst), [".jpg"])
    assert result["verified"] is False
    assert "a.jpg" in result["manquants"]
