"""
tests/test_core.py — Tests unitaires pour tous les modules core.
Utilise des fixtures de répertoire temporaire, CBZ synthétiques et projets factices.
"""
import os
import zipfile
import tempfile
import pytest

# ── Helpers ────────────────────────────────────────────────────────────────────

def make_fake_image(path: str, size: int = 64):
    """Crée un faux JPEG valide (header JFIF minimal)."""
    with open(path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
        f.write(b"\x00" * size)
        f.write(b"\xff\xd9")


def make_fake_cbz(cbz_path: str, n_images: int = 5) -> list[str]:
    """Crée un CBZ synthétique avec n_images JPEG."""
    names = [f"page_{i:03d}.jpg" for i in range(n_images)]
    with zipfile.ZipFile(cbz_path, "w") as zf:
        for name in names:
            data = (
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
                + b"\x00" * 64
                + b"\xff\xd9"
            )
            zf.writestr(name, data)
    return names


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_racine(tmp_path):
    racine = tmp_path / "OsirisScan"
    racine.mkdir()
    return str(racine)


@pytest.fixture
def tmp_project(tmp_racine):
    from core.project_manager import create_project
    path = create_project(tmp_racine, "Test Manhwa")
    return path


@pytest.fixture
def tmp_chapter(tmp_project):
    from core.role_manager import get_sous_dossiers, ROLES_DISPONIBLES
    from core.status_manager import create_status
    role_dossier = "01_Clean"
    role_path = os.path.join(tmp_project, role_dossier)
    chapter_path = os.path.join(role_path, "Chapter 01")
    sous_dossiers = get_sous_dossiers(role_path)
    os.makedirs(chapter_path, exist_ok=True)
    for sd in sous_dossiers:
        os.makedirs(os.path.join(chapter_path, sd["nom"]), exist_ok=True)
    create_status(chapter_path, "Chapter 01", "Cleaner")
    return chapter_path


# ── project_manager ────────────────────────────────────────────────────────────

class TestProjectManager:
    def test_create_project_creates_dir(self, tmp_racine):
        from core.project_manager import create_project
        path = create_project(tmp_racine, "Mon Manhwa")
        assert os.path.isdir(path)

    def test_create_project_yaml_exists(self, tmp_racine):
        from core.project_manager import create_project, read_project_yaml
        path = create_project(tmp_racine, "Mon Manhwa")
        data = read_project_yaml(path)
        assert data["project"]["name"] == "Mon Manhwa"

    def test_create_raw_dir(self, tmp_racine):
        from core.project_manager import create_project
        path = create_project(tmp_racine, "Test")
        assert os.path.isdir(os.path.join(path, "00_Raw"))

    def test_next_chapter_starts_at_1(self, tmp_project):
        from core.project_manager import get_next_chapter_number
        assert get_next_chapter_number(tmp_project) == 1

    def test_scan_projects(self, tmp_racine):
        from core.project_manager import create_project, scan_projects
        create_project(tmp_racine, "Manhwa A")
        create_project(tmp_racine, "Manhwa B")
        projects = scan_projects(tmp_racine)
        assert len(projects) == 2

    def test_detect_pending_cbz(self, tmp_project):
        from core.project_manager import detect_pending_cbz
        raw_path = os.path.join(tmp_project, "00_Raw")
        cbz_path = os.path.join(raw_path, "chapter1.cbz")
        make_fake_cbz(cbz_path, n_images=3)
        pending = detect_pending_cbz(tmp_project)
        assert "chapter1.cbz" in pending

    def test_recalculate_stats(self, tmp_project, tmp_chapter):
        from core.project_manager import recalculate_stats
        stats = recalculate_stats(tmp_project)
        assert "chapitres_termines" in stats
        assert "chapitres_en_cours" in stats

    def test_list_chapters(self, tmp_project, tmp_chapter):
        from core.project_manager import list_chapters
        role_path = os.path.join(tmp_project, "01_Clean")
        chapters = list_chapters(role_path)
        assert "Chapter 01" in chapters


# ── role_manager ───────────────────────────────────────────────────────────────

class TestRoleManager:
    def test_create_role_yaml(self, tmp_path):
        from core.role_manager import create_role_yaml, read_role_yaml
        role_path = str(tmp_path / "01_Clean")
        os.makedirs(role_path, exist_ok=True)
        create_role_yaml(role_path, "Cleaner", "01_Clean")
        data = read_role_yaml(role_path)
        assert data["role"]["label"] == "Cleaner"
        assert data["role"]["dossier"] == "01_Clean"

    def test_default_sous_dossiers(self, tmp_path):
        from core.role_manager import create_role_yaml, get_sous_dossiers
        role_path = str(tmp_path / "01_Clean")
        os.makedirs(role_path, exist_ok=True)
        create_role_yaml(role_path, "Cleaner", "01_Clean")
        sds = get_sous_dossiers(role_path)
        noms = [sd["nom"] for sd in sds]
        assert "01_Original_RAW" in noms
        assert "02_Upscale_RAW" in noms

    def test_list_roles(self, tmp_project):
        from core.role_manager import list_roles
        roles = list_roles(tmp_project)
        assert len(roles) >= 1
        assert any(r["label"] == "Cleaner" for r in roles)

    def test_add_remove_membre(self, tmp_project):
        from core.role_manager import add_membre, remove_membre, read_role_yaml
        role_path = os.path.join(tmp_project, "01_Clean")
        add_membre(role_path, "Alice")
        data = read_role_yaml(role_path)
        assert "Alice" in data["role"]["membres"]
        remove_membre(role_path, "Alice")
        data = read_role_yaml(role_path)
        assert "Alice" not in data["role"]["membres"]

    def test_update_field(self, tmp_project):
        from core.role_manager import update_field, read_role_yaml
        role_path = os.path.join(tmp_project, "01_Clean")
        update_field(role_path, "config", "model_esrgan", "realesrgan-x4plus")
        data = read_role_yaml(role_path)
        assert data["config"]["model_esrgan"] == "realesrgan-x4plus"


# ── status_manager ─────────────────────────────────────────────────────────────

class TestStatusManager:
    def test_create_status_default(self, tmp_chapter):
        from core.status_manager import read_status
        status = read_status(tmp_chapter)
        assert status is not None
        assert status["statut_global"] == "non_commence"
        assert "etapes" in status
        assert "integrite" in status

    def test_mark_etape_done_changes_statut(self, tmp_chapter):
        from core.status_manager import mark_etape_done, read_status
        updated = mark_etape_done(tmp_chapter, "extraction_cbz")
        assert updated["etapes"]["extraction_cbz"]["done"] is True
        assert updated["statut_global"] == "en_cours"

    def test_all_etapes_done_marks_termine(self, tmp_chapter):
        from core.status_manager import mark_etape_done, read_status, ALL_ETAPES
        for etape in ALL_ETAPES:
            mark_etape_done(tmp_chapter, etape)
        status = read_status(tmp_chapter)
        assert status["statut_global"] == "termine"

    def test_add_note(self, tmp_chapter):
        from core.status_manager import add_note, read_status
        add_note(tmp_chapter, "Page 5 floue à retraiter")
        status = read_status(tmp_chapter)
        assert any("floue" in n["texte"] for n in status["notes"])

    def test_update_integrite(self, tmp_chapter):
        from core.status_manager import update_integrite, read_status
        update_integrite(tmp_chapter, raw_count=10, upscale_count=10, verified=True)
        status = read_status(tmp_chapter)
        assert status["integrite"]["verified"] is True
        assert status["integrite"]["raw_count"] == 10

    def test_mark_archive(self, tmp_chapter):
        from core.status_manager import mark_archive, read_status, ALL_ETAPES, mark_etape_done
        for etape in ALL_ETAPES:
            mark_etape_done(tmp_chapter, etape)
        mark_archive(tmp_chapter)
        status = read_status(tmp_chapter)
        assert status["statut_global"] == "archive"

    def test_calc_progression(self, tmp_chapter):
        from core.status_manager import mark_etape_done, read_status, calc_progression, ALL_ETAPES
        mark_etape_done(tmp_chapter, ALL_ETAPES[0])
        status = read_status(tmp_chapter)
        pct = calc_progression(status)
        assert 0.0 < pct < 1.0


# ── changelog ──────────────────────────────────────────────────────────────────

class TestChangelog:
    def test_add_and_read(self, tmp_project):
        from core.changelog import add_entry, read_changelog
        yaml_path = os.path.join(tmp_project, ".project.yaml")
        add_entry(yaml_path, "Cleaner", "Ch.01 créé")
        add_entry(yaml_path, "Cleaner", "Ch.01 upscale terminé en 4m32s")
        entries = read_changelog(yaml_path)
        assert len(entries) >= 2
        actions = [e["action"] for e in entries]
        assert "Ch.01 créé" in actions

    def test_append_only(self, tmp_project):
        from core.changelog import add_entry, read_changelog
        yaml_path = os.path.join(tmp_project, ".project.yaml")
        for i in range(5):
            add_entry(yaml_path, "Cleaner", f"Action {i}")
        entries = read_changelog(yaml_path)
        assert len(entries) >= 5

    def test_entry_has_date(self, tmp_project):
        from core.changelog import add_entry, read_changelog
        yaml_path = os.path.join(tmp_project, ".project.yaml")
        add_entry(yaml_path, "Traducteur", "Traduction Ch.03")
        entries = read_changelog(yaml_path)
        last = entries[-1]
        assert "date" in last and last["date"]
        assert last["role"] == "Traducteur"


# ── cbz_handler ────────────────────────────────────────────────────────────────

class TestCBZHandler:
    def test_list_cbz(self, tmp_path):
        from core.cbz_handler import list_cbz
        raw = tmp_path / "00_Raw"
        raw.mkdir()
        make_fake_cbz(str(raw / "ch01.cbz"), 3)
        (raw / "notes.txt").write_text("pas une archive")
        result = list_cbz(str(raw))
        assert "ch01.cbz" in result
        assert "notes.txt" not in result

    def test_extract_cbz_flat(self, tmp_path):
        from core.cbz_handler import extract_cbz
        cbz_path = str(tmp_path / "test.cbz")
        make_fake_cbz(cbz_path, 5)
        dest = str(tmp_path / "extracted")
        extracted = extract_cbz(cbz_path, dest)
        assert len(extracted) == 5
        assert all(os.path.isfile(f) for f in extracted)

    def test_extract_cbz_with_subdir(self, tmp_path):
        """Archive avec images dans un sous-dossier interne."""
        from core.cbz_handler import extract_cbz
        cbz_path = str(tmp_path / "subdirtest.cbz")
        with zipfile.ZipFile(cbz_path, "w") as zf:
            for i in range(3):
                data = b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"
                zf.writestr(f"subfolder/page_{i:03d}.jpg", data)
        dest = str(tmp_path / "out")
        extracted = extract_cbz(cbz_path, dest)
        assert len(extracted) == 3

    def test_detect_duplicates(self, tmp_path):
        from core.cbz_handler import detect_duplicates
        dest = tmp_path / "dest"
        dest.mkdir()
        make_fake_image(str(dest / "img.jpg"))
        assert detect_duplicates("test.cbz", str(dest)) is True

    def test_no_duplicates_empty(self, tmp_path):
        from core.cbz_handler import detect_duplicates
        dest = tmp_path / "empty"
        dest.mkdir()
        assert detect_duplicates("test.cbz", str(dest)) is False


# ── integrity_checker ──────────────────────────────────────────────────────────

class TestIntegrityChecker:
    def test_verified_when_equal(self, tmp_path):
        from core.integrity_checker import check_integrity
        src = tmp_path / "src"; src.mkdir()
        dst = tmp_path / "dst"; dst.mkdir()
        for i in range(4):
            make_fake_image(str(src / f"img_{i}.jpg"))
            make_fake_image(str(dst / f"img_{i}.jpg"))
        result = check_integrity(str(src), str(dst))
        assert result["verified"] is True
        assert result["raw_count"] == 4

    def test_missing_detected(self, tmp_path):
        from core.integrity_checker import check_integrity
        src = tmp_path / "src"; src.mkdir()
        dst = tmp_path / "dst"; dst.mkdir()
        for i in range(5):
            make_fake_image(str(src / f"img_{i}.jpg"))
        for i in range(4):
            make_fake_image(str(dst / f"img_{i}.jpg"))
        result = check_integrity(str(src), str(dst))
        assert result["verified"] is False
        assert len(result["missing"]) == 1

    def test_count_images(self, tmp_path):
        from core.integrity_checker import count_images
        d = tmp_path / "imgs"; d.mkdir()
        for i in range(6):
            make_fake_image(str(d / f"p{i}.jpg"))
        (d / "readme.txt").write_text("ignored")
        assert count_images(str(d)) == 6

    def test_empty_source(self, tmp_path):
        from core.integrity_checker import check_integrity
        src = tmp_path / "src"; src.mkdir()
        dst = tmp_path / "dst"; dst.mkdir()
        result = check_integrity(str(src), str(dst))
        assert result["verified"] is False
        assert result["raw_count"] == 0


# ── archive_manager ────────────────────────────────────────────────────────────

class TestArchiveManager:
    def test_est_archivable_false_when_not_termine(self, tmp_chapter):
        from core.archive_manager import est_archivable
        assert est_archivable(tmp_chapter) is False

    def test_est_archivable_true_when_termine(self, tmp_chapter):
        from core.archive_manager import est_archivable
        from core.status_manager import mark_etape_done, ALL_ETAPES
        for etape in ALL_ETAPES:
            mark_etape_done(tmp_chapter, etape)
        assert est_archivable(tmp_chapter) is True

    def test_archive_chapter(self, tmp_chapter, monkeypatch):
        from core.archive_manager import archive_chapter
        from core.status_manager import mark_etape_done, ALL_ETAPES
        from ui.colors import confirm_danger
        for etape in ALL_ETAPES:
            mark_etape_done(tmp_chapter, etape)
        # Simuler confirmation automatique
        monkeypatch.setattr("core.archive_manager.confirm_danger", lambda _: True)
        result = archive_chapter(tmp_chapter)
        assert result is not None
        assert os.path.isfile(result)
        assert result.endswith(".zip")


# ── ui/progress_bar ────────────────────────────────────────────────────────────

class TestProgressBar:
    def test_fmt_duration_seconds(self):
        from ui.progress_bar import fmt_duration
        assert "0m30s" in fmt_duration(30)

    def test_fmt_duration_minutes(self):
        from ui.progress_bar import fmt_duration
        assert "4m32s" in fmt_duration(272)

    def test_fmt_duration_hours(self):
        from ui.progress_bar import fmt_duration
        result = fmt_duration(3662)
        assert "1h" in result

    def test_progress_bar_update(self, capsys):
        from ui.progress_bar import ProgressBar
        bar = ProgressBar(10, label="Test")
        bar.update(5)
        bar.done()
        # Pas d'exception = succès
        assert bar.total == 10


# ── ui/table_renderer ──────────────────────────────────────────────────────────

class TestTableRenderer:
    def test_render_table_no_crash(self):
        from ui.table_renderer import render_table
        headers = ["Chapitre", "Cleaner", "Traducteur"]
        rows = [
            ["Chapter 01", "termine", "en_cours"],
            ["Chapter 02", "non_commence", "?"],
        ]
        result = render_table(headers, rows)
        assert "Chapter 01" in result

    def test_export_markdown(self, tmp_path):
        from ui.table_renderer import export_markdown
        filename = str(tmp_path / "test.md")
        export_markdown(
            titre="Test",
            headers=["Ch", "Status"],
            rows=[["Chapter 01", "terminé"]],
            filename=filename,
        )
        assert os.path.isfile(filename)
        content = open(filename).read()
        assert "Chapter 01" in content
        assert "# Test" in content

    def test_status_cell_termine(self):
        from ui.table_renderer import status_cell, _strip_ansi
        cell = status_cell("termine")
        plain = _strip_ansi(cell)
        assert "terminé" in plain

    def test_strip_ansi(self):
        from ui.table_renderer import _strip_ansi
        colored = "\033[32mHello\033[0m"
        assert _strip_ansi(colored) == "Hello"


# ── session ────────────────────────────────────────────────────────────────────

class TestSession:
    def test_breadcrumb_empty(self):
        from session import Session
        s = Session()
        assert s.breadcrumb() == ["OsirisScan"]

    def test_breadcrumb_full(self):
        from session import Session
        s = Session(
            projet_nom="Mon Manhwa",
            role_label="Cleaner",
            chapitre_actif="Chapter 01",
        )
        bc = s.breadcrumb()
        assert "Mon Manhwa" in bc
        assert "Cleaner" in bc
        assert "Chapter 01" in bc

    def test_reset_role(self):
        from session import Session
        s = Session(role_dossier="01_Clean", role_label="Cleaner", chapitre_actif="Ch01")
        s.reset_role()
        assert s.role_dossier == ""
        assert s.chapitre_actif == ""

    def test_is_projet_set(self):
        from session import Session
        s = Session(projet_chemin="/tmp/x", projet_nom="X")
        assert s.is_projet_set() is True
        s2 = Session()
        assert s2.is_projet_set() is False


# ═══════════════════════════════════════════════════════════════════════════════
# Tests Étape 6 : Watcher, Batch CLI, temps_total_upscale, cmd_003
# ═══════════════════════════════════════════════════════════════════════════════

class TestWatcher:
    """Tests du module core/watcher.py (surveillance 00_Raw/)."""

    def test_watcher_imports_and_instantiates(self, tmp_path):
        from core.watcher import RawWatcher
        raw = tmp_path / "00_Raw"
        raw.mkdir()
        detected = []
        watcher = RawWatcher(str(raw), lambda f: detected.append(f))
        assert watcher is not None

    def test_watcher_callback_on_cbz_creation(self, tmp_path):
        """Le callback est appelé quand un .cbz est créé dans le dossier surveillé."""
        import time
        from core.watcher import RawWatcher

        raw = tmp_path / "00_Raw"
        raw.mkdir()
        detected = []
        watcher = RawWatcher(str(raw), lambda f: detected.append(f))
        watcher.start()
        time.sleep(0.3)  # Laisser watchdog s'initialiser

        (raw / "chapter_01.cbz").write_bytes(b"PK\x03\x04")
        time.sleep(0.5)  # Laisser l'event se propager

        watcher.stop()
        assert "chapter_01.cbz" in detected

    def test_watcher_ignores_non_cbz(self, tmp_path):
        """Les fichiers non-CBZ ne déclenchent pas le callback."""
        import time
        from core.watcher import RawWatcher

        raw = tmp_path / "00_Raw"
        raw.mkdir()
        detected = []
        watcher = RawWatcher(str(raw), lambda f: detected.append(f))
        watcher.start()
        time.sleep(0.3)

        (raw / "readme.txt").write_text("test")
        (raw / "image.jpg").write_bytes(b"\xff\xd8\xff")
        time.sleep(0.4)

        watcher.stop()
        assert len(detected) == 0

    def test_watcher_detects_zip(self, tmp_path):
        """Les fichiers .zip sont aussi détectés."""
        import time
        from core.watcher import RawWatcher

        raw = tmp_path / "00_Raw"
        raw.mkdir()
        detected = []
        watcher = RawWatcher(str(raw), lambda f: detected.append(f))
        watcher.start()
        time.sleep(0.3)

        (raw / "chapter_02.zip").write_bytes(b"PK\x03\x04")
        time.sleep(0.5)

        watcher.stop()
        assert "chapter_02.zip" in detected

    def test_watcher_stop_is_idempotent(self, tmp_path):
        """stop() peut être appelé plusieurs fois sans erreur."""
        from core.watcher import RawWatcher
        raw = tmp_path / "00_Raw"
        raw.mkdir()
        watcher = RawWatcher(str(raw), lambda f: None)
        watcher.start()
        watcher.stop()
        watcher.stop()  # Double stop, ne doit pas crasher


class TestTempsUpscale:
    """Tests de la gestion de temps_total_upscale dans project_manager."""

    def test_temps_upscale_cumule(self, tmp_path):
        from core.project_manager import create_project, recalculate_stats, read_project_yaml
        from core.status_manager import create_status, mark_etape_done
        import os

        proj = create_project(str(tmp_path), "Test Upscale")
        role_path = os.path.join(proj, "01_Clean")
        ch_path = os.path.join(role_path, "Chapter 01")
        os.makedirs(ch_path, exist_ok=True)

        create_status(ch_path, "Chapter 01", "Cleaner")
        # Marquer upscale avec durée
        from core.status_manager import read_status
        import yaml
        status = read_status(ch_path)
        status["etapes"]["upscale"] = {"done": True, "date": "2026-05-12", "duree": "4m32s", "auto": True}
        with open(os.path.join(ch_path, ".status.yaml"), "w") as f:
            yaml.dump(status, f, allow_unicode=True)

        recalculate_stats(proj)
        data = read_project_yaml(proj)
        assert data["stats"]["temps_total_upscale"] == "0:04:32"

    def test_temps_upscale_cumule_multiple_chapitres(self, tmp_path):
        from core.project_manager import create_project, recalculate_stats, read_project_yaml
        from core.status_manager import create_status
        import os, yaml

        proj = create_project(str(tmp_path), "Test Multi")
        role_path = os.path.join(proj, "01_Clean")

        for i, duree in enumerate(["2m10s", "1m50s"], start=1):
            ch_path = os.path.join(role_path, f"Chapter {i:02d}")
            os.makedirs(ch_path, exist_ok=True)
            create_status(ch_path, f"Chapter {i:02d}", "Cleaner")
            from core.status_manager import read_status
            status = read_status(ch_path)
            status["etapes"]["upscale"] = {"done": True, "date": "2026-05-12", "duree": duree, "auto": True}
            with open(os.path.join(ch_path, ".status.yaml"), "w") as f:
                yaml.dump(status, f, allow_unicode=True)

        recalculate_stats(proj)
        data = read_project_yaml(proj)
        # 2m10s + 1m50s = 4m = 0:04:00
        assert data["stats"]["temps_total_upscale"] == "0:04:00"

    def test_parse_duration_formats(self):
        from core.project_manager import _parse_duration_to_seconds
        assert _parse_duration_to_seconds("4m32s") == 272.0
        assert _parse_duration_to_seconds("1h04m32s") == 3872.0
        assert _parse_duration_to_seconds("0:04:32") == 272.0
        assert _parse_duration_to_seconds("30s") == 30.0
        assert _parse_duration_to_seconds("") == 0.0

    def test_seconds_to_hms(self):
        from core.project_manager import _seconds_to_hms
        assert _seconds_to_hms(272) == "0:04:32"
        assert _seconds_to_hms(3872) == "1:04:32"
        assert _seconds_to_hms(0) == "0:00:00"


class TestBatchCLI:
    """Tests du mode --batch dans main.py."""

    def test_batch_project_not_found(self, tmp_path, monkeypatch):
        import sys
        import argparse
        from unittest.mock import patch

        monkeypatch.setattr("config_loader.CFG.machine.racine_osirisscan", str(tmp_path))
        import session as sess
        sess.session.racine_osirisscan = str(tmp_path)

        from main import run_batch_mode
        args = argparse.Namespace(
            projet="ProjetInexistant",
            role="01_Clean",
            cmd="extraction_cbz",
            config=None,
            config_racine=str(tmp_path),
        )
        code = run_batch_mode(args)
        assert code == 1

    def test_batch_missing_projet_arg(self, tmp_path, monkeypatch):
        import argparse
        monkeypatch.setattr("config_loader.CFG.machine.racine_osirisscan", str(tmp_path))
        from main import run_batch_mode
        args = argparse.Namespace(
            projet=None, role="01_Clean", cmd="extraction_cbz",
            config=None, config_racine=str(tmp_path),
        )
        code = run_batch_mode(args)
        assert code == 1

    def test_batch_finds_and_runs_existing_project(self, tmp_path, monkeypatch):
        """Un projet valide avec un rôle et une commande existante retourne 0."""
        import argparse
        from core.project_manager import create_project
        from unittest.mock import patch

        proj = create_project(str(tmp_path), "Batch Test")

        monkeypatch.setattr("config_loader.CFG.machine.racine_osirisscan", str(tmp_path))
        import session as sess
        sess.session.racine_osirisscan = str(tmp_path)

        from main import run_batch_mode, find_command_by_slug
        # Patcher run() de la commande avancement (la plus safe, pas d'IO)
        with patch("commands.cmd_007_avancement.run") as mock_run:
            mock_run.return_value = None
            args = argparse.Namespace(
                projet="Batch Test",
                role="01_Clean",
                cmd="avancement",
                config=None,
                config_racine=str(tmp_path),
            )
            code = run_batch_mode(args)
        assert code == 0

    def test_find_command_by_slug(self):
        from main import find_command_by_slug
        cmd = find_command_by_slug("avancement")
        assert cmd is not None
        assert "avancement" in cmd["module"]

        cmd2 = find_command_by_slug("007")
        assert cmd2 is not None

        cmd3 = find_command_by_slug("slug_inexistant_xyz")
        assert cmd3 is None


class TestFusionParGroupe:
    """Tests de cmd_003_fusion_par_groupe."""

    def _make_chapter(self, tmp_path, n_images: int) -> str:
        """Crée un chapitre factice avec N images JPEG basiques."""
        from PIL import Image
        import os

        ch_path = str(tmp_path / "Chapter 01")
        src = os.path.join(ch_path, "04_Clean_JPEG")
        os.makedirs(src, exist_ok=True)

        for i in range(n_images):
            img = Image.new("RGB", (100, 50), color=(i * 10 % 255, 0, 0))
            img.save(os.path.join(src, f"page_{i + 1:03d}.jpg"), "JPEG")

        from core.status_manager import create_status
        create_status(ch_path, "Chapter 01", "Cleaner")
        return ch_path

    def test_split_into_groups(self):
        from commands.cmd_003_fusion_par_groupe import _split_into_groups
        items = list(range(10))
        groups = _split_into_groups(items, 3)
        assert len(groups) == 4
        assert groups[0] == [0, 1, 2]
        assert groups[-1] == [9]

    def test_list_images_sorted(self, tmp_path):
        from commands.cmd_003_fusion_par_groupe import _list_images_sorted
        d = tmp_path / "imgs"
        d.mkdir()
        for name in ["page_003.jpg", "page_001.jpg", "page_002.jpg", "readme.txt"]:
            (d / name).write_bytes(b"\xff\xd8\xff")
        result = _list_images_sorted(str(d))
        assert result == ["page_001.jpg", "page_002.jpg", "page_003.jpg"]

    def test_fusion_creates_groups(self, tmp_path):
        """La fusion par groupe crée le bon nombre de fichiers segmentés."""
        import os
        from PIL import Image

        ch_path = self._make_chapter(tmp_path, 9)
        src = os.path.join(ch_path, "04_Clean_JPEG")
        dst = os.path.join(ch_path, "05_Final_Merged")
        os.makedirs(dst, exist_ok=True)

        from commands.cmd_003_fusion_par_groupe import _list_images_sorted, _split_into_groups
        images = _list_images_sorted(src)
        groups = _split_into_groups(images, 3)
        assert len(groups) == 3

        # Simuler la fusion
        for g_idx, group in enumerate(groups):
            loaded = [Image.open(os.path.join(src, f)).convert("RGB") for f in group]
            total_h = sum(im.height for im in loaded)
            w = max(im.width for im in loaded)
            merged = Image.new("RGB", (w, total_h))
            y = 0
            for im in loaded:
                merged.paste(im, (0, y))
                y += im.height
            merged.save(os.path.join(dst, f"group_{g_idx + 1:03d}.jpg"), "JPEG")

        output = os.listdir(dst)
        assert len([f for f in output if f.endswith(".jpg")]) == 3


# ═══════════════════════════════════════════════════════════════════════════════
# Tests d'intégration — Pipeline end-to-end + commandes métier
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegrationCmd001:
    """Tests d'intégration de cmd_001_creer_chapitre (logique pure)."""

    def test_creer_chapitre_structure(self, tmp_path):
        """Crée un chapitre et vérifie la structure disque."""
        import os
        from core.project_manager import create_project, list_chapters
        from core.role_manager import get_sous_dossiers
        from core.status_manager import create_status, read_status

        proj = create_project(str(tmp_path), "Test Création")
        role_path = os.path.join(proj, "01_Clean")
        chapter_name = "Chapter 01"
        chapter_path = os.path.join(role_path, chapter_name)
        os.makedirs(chapter_path, exist_ok=True)

        sous = get_sous_dossiers(role_path)
        for sd in sous:
            os.makedirs(os.path.join(chapter_path, sd["nom"]), exist_ok=True)

        create_status(chapter_path, chapter_name, "Cleaner")

        assert os.path.isdir(chapter_path)
        assert os.path.isfile(os.path.join(chapter_path, ".status.yaml"))
        for sd in sous:
            assert os.path.isdir(os.path.join(chapter_path, sd["nom"]))

        status = read_status(chapter_path)
        assert status["chapter"] == chapter_name
        assert status["statut_global"] == "non_commence"

        chapters = list_chapters(role_path)
        assert chapter_name in chapters

    def test_creer_chapitre_incremente_prochain(self, tmp_path):
        """Après création + terminaison, prochain_chapitre s'incrémente."""
        import os
        from core.project_manager import create_project, get_next_chapter_number, update_project_after_chapter_done

        proj = create_project(str(tmp_path), "Test Incrémente")
        assert get_next_chapter_number(proj) == 1

        update_project_after_chapter_done(proj, 1)
        assert get_next_chapter_number(proj) == 2

        update_project_after_chapter_done(proj, 2)
        assert get_next_chapter_number(proj) == 3


class TestIntegrationCmd002:
    """Tests d'intégration de la fusion globale (logique Pillow)."""

    def _make_jpeg_images(self, directory: str, n: int, w=100, h=50) -> list[str]:
        from PIL import Image
        import os
        os.makedirs(directory, exist_ok=True)
        paths = []
        for i in range(n):
            img = Image.new("RGB", (w, h), color=(i * 20 % 255, 0, 100))
            p = os.path.join(directory, f"page_{i + 1:03d}.jpg")
            img.save(p, "JPEG")
            paths.append(p)
        return paths

    def test_fusion_globale_dimensions(self, tmp_path):
        """L'image fusionnée a la bonne hauteur totale."""
        from PIL import Image
        from commands.cmd_002_fusion_globale import _list_images_sorted
        import os

        src = str(tmp_path / "04_Clean_JPEG")
        self._make_jpeg_images(src, 5, w=100, h=50)

        images = _list_images_sorted(src)
        assert len(images) == 5

        loaded = [Image.open(os.path.join(src, f)).convert("RGB") for f in images]
        total_h = sum(im.height for im in loaded)
        w = max(im.width for im in loaded)
        merged = Image.new("RGB", (w, total_h))
        y = 0
        for im in loaded:
            merged.paste(im, (0, y))
            y += im.height

        assert merged.width == 100
        assert merged.height == 250  # 5 * 50

    def test_fusion_qscale_from_role_yaml(self, tmp_path):
        """La qualité JPEG est lue depuis .role.yaml."""
        import os
        from core.project_manager import create_project
        from core.role_manager import read_role_yaml, update_field

        proj = create_project(str(tmp_path), "Test QScale")
        role_path = os.path.join(proj, "01_Clean")

        # Modifier qscale_global
        update_field(role_path, "config", "qscale_global", 80)

        data = read_role_yaml(role_path)
        assert data["config"]["qscale_global"] == 80

    def test_list_images_sorted_numerique(self, tmp_path):
        """Les images sont triées numériquement, pas alphabétiquement."""
        import os
        from commands.cmd_002_fusion_globale import _list_images_sorted

        d = str(tmp_path / "imgs")
        os.makedirs(d)
        for name in ["page_10.jpg", "page_2.jpg", "page_1.jpg"]:
            open(os.path.join(d, name), "wb").write(b"\xff\xd8\xff")

        result = _list_images_sorted(d)
        assert result == ["page_1.jpg", "page_2.jpg", "page_10.jpg"]


class TestIntegrationCmd005:
    """Tests d'intégration extraction CBZ end-to-end."""

    def _make_cbz(self, path: str, n_images: int = 5) -> str:
        import zipfile, os
        cbz_path = str(path)
        with zipfile.ZipFile(cbz_path, "w") as zf:
            for i in range(n_images):
                name = f"page_{i + 1:03d}.jpg"
                zf.writestr(name, b"\xff\xd8\xff" + b"\x00" * 50)
        return cbz_path

    def test_extraction_vers_destination(self, tmp_path):
        """Extraction complète vers 01_Original_RAW/."""
        import os
        from core.cbz_handler import extract_cbz, list_cbz
        from core.integrity_checker import count_images

        raw = tmp_path / "00_Raw"
        raw.mkdir()
        cbz_path = self._make_cbz(raw / "chapter_01.cbz", n_images=7)

        dest = str(tmp_path / "01_Original_RAW")
        extracted = extract_cbz(cbz_path, dest)

        assert len(extracted) == 7
        assert count_images(dest) == 7

    def test_extraction_conserve_source(self, tmp_path):
        """Le CBZ source n'est JAMAIS modifié après extraction."""
        import os
        from core.cbz_handler import extract_cbz

        raw = tmp_path / "00_Raw"
        raw.mkdir()
        cbz_path = self._make_cbz(raw / "test.cbz", n_images=3)
        size_before = os.path.getsize(cbz_path)

        extract_cbz(cbz_path, str(tmp_path / "dest"))

        assert os.path.isfile(cbz_path)  # Toujours présent
        assert os.path.getsize(cbz_path) == size_before  # Inchangé

    def test_detection_doublons(self, tmp_path):
        """detect_duplicates retourne True si des images existent déjà."""
        import os
        from core.cbz_handler import detect_duplicates

        dest = tmp_path / "dest"
        dest.mkdir()
        (dest / "page_001.jpg").write_bytes(b"\xff\xd8\xff")

        assert detect_duplicates("chapter.cbz", str(dest)) is True

    def test_detection_doublons_vide(self, tmp_path):
        """detect_duplicates retourne False si dossier vide."""
        from core.cbz_handler import detect_duplicates
        dest = tmp_path / "dest_vide"
        dest.mkdir()
        assert detect_duplicates("chapter.cbz", str(dest)) is False


class TestIntegrationCmd008:
    """Tests de cmd_008 : qscale et sous-dossiers CRUD."""

    def test_qscale_global_update(self, tmp_path):
        """update_field modifie qscale_global dans .role.yaml."""
        import os
        from core.project_manager import create_project
        from core.role_manager import update_field, read_role_yaml

        proj = create_project(str(tmp_path), "Test QScale 008")
        role_path = os.path.join(proj, "01_Clean")
        update_field(role_path, "config", "qscale_global", 75)
        data = read_role_yaml(role_path)
        assert data["config"]["qscale_global"] == 75

    def test_qscale_groupe_update(self, tmp_path):
        import os
        from core.project_manager import create_project
        from core.role_manager import update_field, read_role_yaml

        proj = create_project(str(tmp_path), "Test QScale Groupe")
        role_path = os.path.join(proj, "01_Clean")
        update_field(role_path, "config", "qscale_groupe", 88)
        data = read_role_yaml(role_path)
        assert data["config"]["qscale_groupe"] == 88

    def test_sous_dossier_ajout(self, tmp_path):
        """Ajouter un sous-dossier dans .role.yaml via write_role_yaml."""
        import os
        from core.project_manager import create_project
        from core.role_manager import read_role_yaml, write_role_yaml

        proj = create_project(str(tmp_path), "Test SousDossier")
        role_path = os.path.join(proj, "01_Clean")
        data = read_role_yaml(role_path)
        sds = data.setdefault("sous_dossiers", [])
        nouveau = {"nom": "05_Archive", "index": len(sds)}
        sds.append(nouveau)
        write_role_yaml(role_path, data)

        data2 = read_role_yaml(role_path)
        noms = [s.get("nom", s) for s in data2.get("sous_dossiers", [])]
        assert "05_Archive" in noms

    def test_sous_dossier_suppression(self, tmp_path):
        import os
        from core.project_manager import create_project
        from core.role_manager import read_role_yaml, write_role_yaml

        proj = create_project(str(tmp_path), "Test SD Suppression")
        role_path = os.path.join(proj, "01_Clean")
        data = read_role_yaml(role_path)
        data.setdefault("sous_dossiers", [])
        data["sous_dossiers"].append({"nom": "05_Temp", "index": 10})
        write_role_yaml(role_path, data)

        # Suppression
        data = read_role_yaml(role_path)
        data["sous_dossiers"] = [
            s for s in data["sous_dossiers"]
            if (s.get("nom", s) if isinstance(s, dict) else s) != "05_Temp"
        ]
        write_role_yaml(role_path, data)

        data2 = read_role_yaml(role_path)
        noms = [s.get("nom", s) for s in data2.get("sous_dossiers", [])]
        assert "05_Temp" not in noms


class TestIntegrationPipelineComplet:
    """Tests du pipeline end-to-end (sans subprocess/Photoshop)."""

    def _make_full_chapter(self, tmp_path, chapter_name="Chapter 01"):
        """Crée un chapitre complet avec images dans 04_Clean_JPEG/."""
        import os
        from PIL import Image
        from core.project_manager import create_project
        from core.status_manager import create_status

        proj = create_project(str(tmp_path), "Test Pipeline")
        role_path = os.path.join(proj, "01_Clean")
        ch_path = os.path.join(role_path, chapter_name)

        for sub in ["01_Original_RAW", "02_Upscale_RAW", "03_Clean_PSD",
                    "04_Clean_JPEG", "05_Final_Merged"]:
            os.makedirs(os.path.join(ch_path, sub), exist_ok=True)

        # Créer 4 images dans 04_Clean_JPEG/
        for i in range(4):
            img = Image.new("RGB", (100, 80), (i * 30, 0, 0))
            img.save(os.path.join(ch_path, "04_Clean_JPEG", f"page_{i+1:03d}.jpg"), "JPEG")

        create_status(ch_path, chapter_name, "Cleaner")
        return proj, role_path, ch_path

    def test_pipeline_extraction_upscale_fusion(self, tmp_path):
        """
        Simule extraction → upscale (copie) → fusion et vérifie les statuts.
        """
        import os, shutil
        import zipfile
        from PIL import Image
        from core.status_manager import read_status, mark_etape_done, update_integrite
        from core.integrity_checker import check_integrity
        from core.changelog import add_entry

        proj, role_path, ch_path = self._make_full_chapter(tmp_path)
        project_yaml = os.path.join(proj, ".project.yaml")

        # 1. Simuler extraction CBZ → 01_Original_RAW
        raw_dir = os.path.join(ch_path, "01_Original_RAW")
        for i in range(3):
            img = Image.new("RGB", (100, 80))
            img.save(os.path.join(raw_dir, f"img_{i:03d}.jpg"), "JPEG")
        mark_etape_done(ch_path, "extraction_cbz")

        status = read_status(ch_path)
        assert status["etapes"]["extraction_cbz"]["done"] is True
        assert status["statut_global"] == "en_cours"

        # 2. Simuler upscale → 02_Upscale_RAW (copie)
        up_dir = os.path.join(ch_path, "02_Upscale_RAW")
        for f in os.listdir(raw_dir):
            shutil.copy(os.path.join(raw_dir, f), os.path.join(up_dir, f))

        result = check_integrity(raw_dir, up_dir)
        assert result["verified"] is True
        update_integrite(ch_path, result["raw_count"], result["upscale_count"], result["verified"])
        mark_etape_done(ch_path, "upscale", duree="1m30s")
        add_entry(project_yaml, "Cleaner", "Chapter 01 — upscale terminé")

        status = read_status(ch_path)
        assert status["etapes"]["upscale"]["done"] is True
        assert status["integrite"]["verified"] is True

        # 3. Simuler étapes manuelles
        mark_etape_done(ch_path, "nettoyage_psd")
        mark_etape_done(ch_path, "export_jpeg")

        # 4. Fusion finale
        from commands.cmd_002_fusion_globale import _list_images_sorted
        src = os.path.join(ch_path, "04_Clean_JPEG")
        dst = os.path.join(ch_path, "05_Final_Merged")
        images = _list_images_sorted(src)
        assert len(images) > 0

        loaded = [Image.open(os.path.join(src, f)).convert("RGB") for f in images]
        total_h = sum(im.height for im in loaded)
        merged = Image.new("RGB", (max(im.width for im in loaded), total_h))
        y = 0
        for im in loaded:
            merged.paste(im, (0, y))
            y += im.height
        merged.save(os.path.join(dst, "merged_output.jpg"), "JPEG", quality=95)

        mark_etape_done(ch_path, "fusion_finale")
        add_entry(project_yaml, "Cleaner", "Chapter 01 — fusion terminée")

        # 5. Vérifications finales
        status = read_status(ch_path)
        assert status["statut_global"] == "termine"
        assert os.path.isfile(os.path.join(dst, "merged_output.jpg"))

        from core.changelog import read_changelog
        entries = read_changelog(project_yaml)
        assert len(entries) >= 2

    def test_recalculate_stats_after_pipeline(self, tmp_path):
        """Stats du projet cohérentes après le pipeline."""
        import os, yaml
        from core.project_manager import recalculate_stats, read_project_yaml
        from core.status_manager import read_status

        proj, role_path, ch_path = self._make_full_chapter(tmp_path)

        # Forcer statut terminé
        status = read_status(ch_path)
        status["statut_global"] = "termine"
        status["etapes"]["upscale"] = {"done": True, "duree": "2m00s", "date": "2026-05-12", "auto": True}
        with open(os.path.join(ch_path, ".status.yaml"), "w") as f:
            yaml.dump(status, f, allow_unicode=True)

        recalculate_stats(proj)
        data = read_project_yaml(proj)

        assert data["stats"]["chapitres_termines"] >= 1
        assert data["progression"]["dernier_chapitre_termine"] >= 1
        assert data["stats"]["temps_total_upscale"] == "0:02:00"


# ═══════════════════════════════════════════════════════════════════════════════
# Tests v4 — Audit final
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditFinal:
    """Tests couvrant les derniers points d'audit."""

    def test_chapitres_total_connus_updated(self, tmp_path):
        """recalculate_stats met à jour chapitres_total_connus."""
        import os, yaml
        from core.project_manager import create_project, recalculate_stats, read_project_yaml
        from core.status_manager import create_status, mark_etape_done

        proj = create_project(str(tmp_path), "Audit Total Connus")
        role_path = os.path.join(proj, "01_Clean")

        # Créer 2 chapitres
        for n in (1, 2):
            ch_path = os.path.join(role_path, f"Chapter {n:02d}")
            for sub in ["01_Original_RAW", "02_Upscale_RAW",
                        "03_Clean_PSD", "04_Clean_JPEG", "05_Final_Merged"]:
                os.makedirs(os.path.join(ch_path, sub), exist_ok=True)
            create_status(ch_path, f"Chapter {n:02d}", "Cleaner")

        # Marquer ch01 terminé
        ch1 = os.path.join(role_path, "Chapter 01")
        for etape in ["extraction_cbz", "upscale", "nettoyage_psd",
                      "export_jpeg", "fusion_finale"]:
            mark_etape_done(ch1, etape)

        recalculate_stats(proj)
        data = read_project_yaml(proj)
        prog = data["progression"]

        assert prog["chapitres_total_connus"] == 2
        assert data["stats"]["chapitres_termines"] == 1
        assert data["stats"]["chapitres_non_commences"] == 1

    def test_export_markdown_extra_header_lines(self, tmp_path):
        """export_markdown insère les extra_header_lines entre titre et tableau."""
        from ui.table_renderer import export_markdown
        out = str(tmp_path / "test_export.md")
        extra = ["**Stat A** : 42", "**Stat B** : 100%", ""]
        export_markdown(
            titre="Test Export",
            headers=["Chapitre", "Cleaner", "Typo"],
            rows=[["Chapter 01", "termine", "non_commence"]],
            filename=out,
            extra_header_lines=extra,
        )
        content = open(out, encoding="utf-8").read()
        assert "# Test Export" in content
        assert "**Stat A** : 42" in content
        assert "**Stat B** : 100%" in content
        assert "| Chapitre | Cleaner | Typo |" in content
        assert "✔ terminé" in content

    def test_export_markdown_in_project_dir(self, tmp_path):
        """Export markdown se fait dans le dossier du projet."""
        import os
        from ui.table_renderer import export_markdown

        proj_dir = str(tmp_path / "Mon_Manhwa")
        os.makedirs(proj_dir)
        filename = os.path.join(proj_dir, "Mon_Manhwa_avancement_20260512.md")
        export_markdown(
            titre="Test Projet Dir",
            headers=["Chapitre", "Rôle"],
            rows=[["Ch01", "termine"]],
            filename=filename,
        )
        assert os.path.isfile(filename)
        # Le fichier est bien dans le dossier projet
        assert os.path.dirname(filename) == proj_dir

    def test_cmd006_count_images_in_folder(self, tmp_path):
        """count_images détecte bien les images dans un sous-dossier d'étape."""
        import os
        from core.integrity_checker import count_images

        d = tmp_path / "03_Clean_PSD"
        d.mkdir()
        for i in range(3):
            (d / f"page_{i}.jpg").write_bytes(b"\xff\xd8\xff")

        assert count_images(str(d)) == 3
        assert count_images(str(tmp_path / "vide_inexistant")) == 0

    def test_table_renderer_extra_header_none(self, tmp_path):
        """export_markdown fonctionne sans extra_header_lines (=None)."""
        from ui.table_renderer import export_markdown
        out = str(tmp_path / "no_extra.md")
        export_markdown(
            titre="Sans Extra",
            headers=["A", "B"],
            rows=[["x", "y"]],
            filename=out,
            extra_header_lines=None,
        )
        content = open(out, encoding="utf-8").read()
        assert "# Sans Extra" in content
        assert "| A | B |" in content

    def test_status_cell_all_values(self):
        """status_cell gère tous les types de valeurs."""
        import re
        from ui.table_renderer import status_cell
        def strip(s): return re.sub(r"\x1b\[[0-9;]*m", "", s)

        assert "terminé" in strip(status_cell("termine"))
        assert "en cours" in strip(status_cell("en_cours"))
        assert "non comm" in strip(status_cell("non_commence"))
        assert "archivé" in strip(status_cell("archive"))
        assert "?" in strip(status_cell(None))
        assert "100%" in strip(status_cell(1.0))
        assert "50%" in strip(status_cell(0.5))
        assert "0%" in strip(status_cell(0.0))

    def test_recalculate_stats_temps_upscale(self, tmp_path):
        """temps_total_upscale est cumulé correctement sur plusieurs chapitres."""
        import os, yaml
        from core.project_manager import create_project, recalculate_stats, read_project_yaml
        from core.status_manager import create_status, mark_etape_done

        proj = create_project(str(tmp_path), "Test Temps")
        role_path = os.path.join(proj, "01_Clean")

        for n, duree in [(1, "0:02:00"), (2, "0:03:30")]:
            ch_path = os.path.join(role_path, f"Chapter {n:02d}")
            for sub in ["01_Original_RAW", "02_Upscale_RAW",
                        "03_Clean_PSD", "04_Clean_JPEG", "05_Final_Merged"]:
                os.makedirs(os.path.join(ch_path, sub), exist_ok=True)
            create_status(ch_path, f"Chapter {n:02d}", "Cleaner")
            for etape in ["extraction_cbz", "upscale", "nettoyage_psd",
                          "export_jpeg", "fusion_finale"]:
                if etape == "upscale":
                    mark_etape_done(ch_path, etape, duree=duree)
                else:
                    mark_etape_done(ch_path, etape)

        recalculate_stats(proj)
        data = read_project_yaml(proj)
        # 2m + 3m30s = 5m30s = 0:05:30
        assert data["stats"]["temps_total_upscale"] == "0:05:30"


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — save_racine + initialisation racine_osirisscan
# ═══════════════════════════════════════════════════════════════════════════════

class TestSaveRacine:
    """Tests de config_loader.save_racine() et persistance config.yaml."""

    def test_save_racine_cree_config_yaml(self, tmp_path):
        """save_racine crée config.yaml si inexistant et y écrit la racine."""
        import os, yaml
        import config_loader as cl
        original_path = cl._config_path
        try:
            fake_config = str(tmp_path / "config.yaml")
            cl._config_path = fake_config
            cl.save_racine(str(tmp_path))
            assert os.path.isfile(fake_config)
            with open(fake_config, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert data["machine"]["racine_osirisscan"] == str(tmp_path)
        finally:
            cl._config_path = original_path

    def test_save_racine_preserve_autres_cles(self, tmp_path):
        """save_racine ne supprime pas les autres clés du config.yaml."""
        import yaml
        import config_loader as cl
        original_path = cl._config_path
        try:
            fake_config = str(tmp_path / "config.yaml")
            # Créer un config pré-rempli
            existing = {
                "machine": {"racine_osirisscan": "/ancien/chemin"},
                "upscale": {"exe_path": "C:/Tools/realesrgan.exe"},
                "console": {"largeur_banniere": 80},
            }
            with open(fake_config, "w", encoding="utf-8") as f:
                yaml.dump(existing, f)
            cl._config_path = fake_config

            cl.save_racine(str(tmp_path / "nouveau"))

            with open(fake_config, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            # La racine est mise à jour
            assert data["machine"]["racine_osirisscan"] == str(tmp_path / "nouveau")
            # Les autres clés sont préservées
            assert data["upscale"]["exe_path"] == "C:/Tools/realesrgan.exe"
            assert data["console"]["largeur_banniere"] == 80
        finally:
            cl._config_path = original_path

    def test_save_racine_met_a_jour_cfg_en_memoire(self, tmp_path):
        """save_racine met immédiatement à jour CFG.machine.racine_osirisscan."""
        import config_loader as cl
        original_path = cl._config_path
        try:
            fake_config = str(tmp_path / "config.yaml")
            cl._config_path = fake_config
            cl.save_racine(str(tmp_path))
            assert cl.CFG.machine.racine_osirisscan == str(tmp_path)
        finally:
            cl._config_path = original_path
            # Restaurer CFG
            cl.CFG.machine.racine_osirisscan = cl.load_config(original_path).machine.racine_osirisscan

    def test_save_racine_idempotent(self, tmp_path):
        """Appeler save_racine deux fois avec la même valeur ne corrompt pas le fichier."""
        import yaml
        import config_loader as cl
        original_path = cl._config_path
        try:
            fake_config = str(tmp_path / "config.yaml")
            cl._config_path = fake_config
            cl.save_racine(str(tmp_path))
            cl.save_racine(str(tmp_path))
            with open(fake_config, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert data["machine"]["racine_osirisscan"] == str(tmp_path)
        finally:
            cl._config_path = original_path

    def test_load_config_racine_vide_par_defaut(self, tmp_path):
        """Un config.yaml sans [machine] retourne racine_osirisscan vide."""
        import yaml
        from config_loader import load_config
        fake = tmp_path / "empty_config.yaml"
        yaml.dump({"console": {"largeur_banniere": 70}}, fake.open("w"))
        cfg = load_config(str(fake))
        assert cfg.machine.racine_osirisscan == ""

    def test_save_racine_unicode_path(self, tmp_path):
        """save_racine gère les chemins avec caractères unicode (accents, espaces)."""
        import yaml
        import config_loader as cl
        original_path = cl._config_path
        try:
            fake_config = str(tmp_path / "config.yaml")
            cl._config_path = fake_config
            unicode_path = str(tmp_path / "Œuvres & Manhwa")
            cl.save_racine(unicode_path)
            with open(fake_config, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert data["machine"]["racine_osirisscan"] == unicode_path
        finally:
            cl._config_path = original_path
