import pytest
try:
    from textual.testing import AppTest
    HAS_TEXTUAL = True
except ImportError:
    HAS_TEXTUAL = False

@pytest.mark.skipif(not HAS_TEXTUAL, reason="textual non disponible")
async def test_select_project_screen_mount():
    from ui.app import ManhwaApp
    async with ManhwaApp().run_test() as pilot:
        assert pilot.app is not None

def test_modal_danger_importable():
    from ui.modals import DangerModal, ConfirmModal
    assert issubclass(DangerModal, ConfirmModal)
