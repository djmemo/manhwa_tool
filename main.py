import argparse, os, importlib.util, glob
from config_loader import CFG
from session import SESSION

def _run_batch(cmd_name: str):
    pattern = os.path.join(os.path.dirname(__file__), "commands", f"*{cmd_name}*.py")
    print(f"Looking for batch command in: {pattern}")
    for path in sorted(glob.glob(pattern)):
        print(f"Executing batch command: {path}")
        name = os.path.basename(path)[:-3]
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print(f"Module {name} executed successfully.")
        mod.run(); break

def main():
    parser = argparse.ArgumentParser(description="Manhwa Tool v3")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--cmd", default="")
    parser.add_argument("--config", default="")
    args = parser.parse_args()
    SESSION.racine_scantrad = CFG.machine.get("racine_scantrad", "")

    if args.batch and args.cmd:
        print(f"Running batch command: {args.cmd}")
        _run_batch(args.cmd)
    else:
        from ui.app import ManhwaApp
        ManhwaApp().run()

if __name__ == "__main__":
    main()
