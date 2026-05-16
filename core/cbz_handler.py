import os
import zipfile
from core.utils import EXTS_IMAGE

def lister_archives(raw_chemin: str) -> list[str]:
    if not os.path.exists(raw_chemin):
        return []
    return sorted(f for f in os.listdir(raw_chemin) if f.lower().endswith((".cbz", ".zip")))

def detecter_doublons(archive: str, destination: str) -> bool:
    if not os.path.exists(destination):
        return False
    return any(f.lower().endswith(EXTS_IMAGE) for f in os.listdir(destination))

def extraire(archive_chemin: str, destination: str, callback=None) -> int:
    real_src = os.path.realpath(archive_chemin)
    if not os.path.exists(real_src):
        return 0

    os.makedirs(destination, exist_ok=True)
    count = 0

    with zipfile.ZipFile(real_src, "r") as zf:
        images = sorted(n for n in zf.namelist() if n.lower().endswith(EXTS_IMAGE))
        total = len(images)
        for member in images:
            basename = os.path.basename(member)
            dest_path = os.path.join(destination, basename)
            with open(dest_path, "wb") as out:
                out.write(zf.read(member))
            count += 1
            if callback:
                callback(count, total)
    return count
