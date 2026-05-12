"""
core/watcher.py — Surveillance de 00_Raw/ avec watchdog.
Notifie via callback(filename) à chaque nouveau .cbz détecté.
"""
import os
from typing import Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class _CBZHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str], None]):
        self._callback = callback

    def on_created(self, event):
        if not event.is_directory:
            name = os.path.basename(event.src_path)
            if name.lower().endswith((".cbz", ".zip")):
                self._callback(name)


class RawWatcher:
    """Surveille 00_Raw/ et appelle callback(filename) à chaque nouveau CBZ."""

    def __init__(self, raw_path: str, callback: Callable[[str], None]):
        self._raw_path = raw_path
        self._callback = callback
        self._observer = Observer()

    def start(self):
        handler = _CBZHandler(self._callback)
        self._observer.schedule(handler, self._raw_path, recursive=False)
        self._observer.start()

    def stop(self):
        self._observer.stop()
        self._observer.join()
