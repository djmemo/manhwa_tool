import os, pytest
from core import cbz_handler
from PIL import Image

def test_lister_archives(tmp_project, tmp_cbz):
    import shutil
    shutil.copy(tmp_cbz, os.path.join(tmp_project["raw"], "ch01.cbz"))
    archives = cbz_handler.lister_archives(tmp_project["raw"])
    assert "ch01.cbz" in archives
    assert cbz_handler.lister_archives("/chemin/invalide") == []

def test_detecter_doublons(tmp_project):
    dst = os.path.join(tmp_project["projet"], "dest")
    os.makedirs(dst, exist_ok=True)
    assert cbz_handler.detecter_doublons("dummy.cbz", dst) is False
    Image.new("RGB", (10,10)).save(os.path.join(dst, "test.jpg"))
    assert cbz_handler.detecter_doublons("dummy.cbz", dst) is True

def test_extraire(tmp_project, tmp_cbz):
    dst = os.path.join(tmp_project["projet"], "out")
    count = cbz_handler.extraire(tmp_cbz, dst)
    assert count == 5
    assert cbz_handler.extraire("/chemin/invalide.cbz", dst) == 0

def test_ne_modifie_pas_source(tmp_project, tmp_cbz):
    import shutil
    cbz = os.path.join(tmp_project["raw"], "test.cbz")
    shutil.copy(tmp_cbz, cbz)
    taille_avant = os.path.getsize(cbz)
    cbz_handler.extraire(cbz, os.path.join(tmp_project["projet"], "out2"))
    assert os.path.getsize(cbz) == taille_avant
