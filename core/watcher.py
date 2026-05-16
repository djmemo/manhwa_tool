import os
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class _CBZHandler(FileSystemEventHandler):
        def __init__(self, raw_chemin: str, callback):
            self._raw_chemin = raw_chemin
            self._callback   = callback
            self._seen: set  = set()

        def on_created(self, event):
            if event.is_directory:
                return
            if not event.src_path.lower().endswith((".cbz", ".zip")):
                return
            abs_path = os.path.abspath(event.src_path)
            if abs_path in self._seen:
                return
            self._seen.add(abs_path)
            # Attendre que l'écriture soit terminée (évite les lectures partielles)
            self._wait_stable(abs_path)
            self._callback(abs_path)   # ← chemin COMPLET

        @staticmethod
        def _wait_stable(path: str, timeout: float = 30.0, interval: float = 0.5) -> None:
            """Attend que la taille du fichier soit stable (fin de copie)."""
            prev, elapsed = -1, 0.0
            while elapsed < timeout:
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = -1
                if size == prev and size >= 0:
                    return
                prev = size
                time.sleep(interval)
                elapsed += interval

    def demarrer_watcher(raw_chemin: str, callback) -> Observer:
        handler = _CBZHandler(raw_chemin, callback)
        obs = Observer()
        obs.schedule(handler, raw_chemin, recursive=False)
        obs.start()
        return obs

    def arreter_watcher(observer: Observer) -> None:
        observer.stop()
        observer.join()

except ImportError:
    def demarrer_watcher(raw_chemin: str, callback):
        return None
    def arreter_watcher(observer) -> None:
        pass
