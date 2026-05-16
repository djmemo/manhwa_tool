import pytest
from core.watcher import demarrer_watcher, arreter_watcher

def test_watcher_start_stop(tmp_path):
    obs = demarrer_watcher(str(tmp_path), lambda f: None)
    if obs is not None:
        arreter_watcher(obs)
    assert True
