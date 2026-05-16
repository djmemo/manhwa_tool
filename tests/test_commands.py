import glob, os, importlib.util, pytest


def load_all_commands():
    pattern = os.path.join(os.path.dirname(__file__), "..", "commands", "cmd_*.py")
    commands = []
    for path in sorted(glob.glob(pattern)):
        name = os.path.basename(path)[:-3]
        spec = importlib.util.spec_from_file_location(name, path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        commands.append(mod)
    return commands


def test_auto_decouverte():
    cmds = load_all_commands()
    assert len(cmds) == 12   # cmd_000 à cmd_011


def test_label_non_vide():
    for cmd in load_all_commands():
        assert hasattr(cmd, "LABEL") and cmd.LABEL != ""


def test_description_non_vide():
    for cmd in load_all_commands():
        assert hasattr(cmd, "DESCRIPTION") and cmd.DESCRIPTION != ""


def test_run_callable():
    for cmd in load_all_commands():
        assert callable(cmd.run)
