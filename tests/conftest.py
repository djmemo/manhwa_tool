import pytest, os, zipfile
from PIL import Image


@pytest.fixture
def tmp_project(tmp_path):
    racine = tmp_path / "OsirisScan"
    racine.mkdir()
    projet = racine / "TestProject"
    projet.mkdir()
    raw   = projet / "00_Raw"
    raw.mkdir()
    clean = projet / "01_Clean"
    clean.mkdir()
    return {
        "racine": str(racine),
        "projet": str(projet),
        "raw":    str(raw),
        "clean":  str(clean),
    }


@pytest.fixture
def tmp_cbz(tmp_path):
    cbz_path = tmp_path / "test_chapter.cbz"
    with zipfile.ZipFile(str(cbz_path), "w") as zf:
        for i in range(5):
            img      = Image.new("RGB", (100, 200), color=(i * 50, 0, 0))
            img_path = tmp_path / f"page_{i:03d}.jpg"
            img.save(str(img_path))
            zf.write(str(img_path), f"page_{i:03d}.jpg")
    return str(cbz_path)


@pytest.fixture
def tmp_clean_jpeg(tmp_path):
    """
    Crée un dossier 03_Clean_JPEG avec :
      - 001__001.jpg, 001__002.jpg, 001__003.jpg  (page 001 en 3 parties)
      - 002__001.jpg, 002__002.jpg               (page 002 en 2 parties)
      - 003.jpg                                  (page simple, sans découpe)
    Retourne le chemin du dossier src et le dossier dst vide.
    """
    src = tmp_path / "03_Clean_JPEG"
    dst = tmp_path / "04_Final_Merged"
    src.mkdir()
    dst.mkdir()

    # Page 001 découpée en 3 parties
    for part in range(1, 4):
        img = Image.new("RGB", (200, 300), color=(part * 60, 0, 0))
        img.save(str(src / f"001__{part:03d}.jpg"))

    # Page 002 découpée en 2 parties
    for part in range(1, 3):
        img = Image.new("RGB", (200, 400), color=(0, part * 60, 0))
        img.save(str(src / f"002__{part:03d}.jpg"))

    # Page 003 simple
    img = Image.new("RGB", (200, 500), color=(0, 0, 120))
    img.save(str(src / "003.jpg"))

    return {"src": str(src), "dst": str(dst)}
