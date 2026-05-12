"""
cmd_010_surveiller_raw.py — Surveillance en temps réel de 00_Raw/.
Lance le watcher watchdog depuis le menu principal.
"""
import os
import time
import threading
from session import session
from core.watcher import RawWatcher
from core.cbz_handler import list_cbz
from ui.colors import ok, err, warn, info, title
from ui.menu_engine import _clear

LABEL = "👁   Surveiller 00_Raw/ (watcher)"
DESCRIPTION = "Surveillance réactive : alerte console à chaque nouveau CBZ détecté"


def run():
    _clear()
    raw_path = os.path.join(session.projet_chemin, "00_Raw")

    if not os.path.isdir(raw_path):
        print(err(f"\n  Dossier 00_Raw/ introuvable : {raw_path}"))
        input("  [Entrée] ")
        return

    pending = list_cbz(raw_path)
    print(title(f"\n  👁   Surveillance — {session.projet_nom} / 00_Raw/\n"))
    if pending:
        print(warn(f"  {len(pending)} archive(s) déjà en attente :"))
        for c in pending:
            print(f"    • {c}")
    else:
        print(info("  Aucune archive en attente actuellement."))

    print(info("\n  Surveillance active. Appuyez sur Entrée pour arrêter.\n"))

    detected: list[str] = []
    lock = threading.Lock()

    def on_new_cbz(filename: str):
        ts = time.strftime("%H:%M:%S")
        with lock:
            detected.append(filename)
            print(warn(f"  [{ts}]  📦  Nouveau CBZ : {filename}"))
            print(info(f"  Total détecté(s) cette session : {len(detected)}"))

    watcher = RawWatcher(raw_path, on_new_cbz)
    watcher.start()

    try:
        input()  # Bloque jusqu'à Entrée
    finally:
        watcher.stop()

    if detected:
        print(ok(f"\n  Surveillance arrêtée. {len(detected)} CBZ détecté(s) :"))
        for f in detected:
            print(f"    • {f}")
    else:
        print(info("\n  Surveillance arrêtée. Aucun CBZ détecté pendant la session."))
    input("  [Entrée] ")
