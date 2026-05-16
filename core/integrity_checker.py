import os
from core.utils import EXTS_IMAGE

def compter_images(dossier: str, extensions: tuple[str, ...] | list[str] = EXTS_IMAGE) -> int:
    if not os.path.exists(dossier):
        return 0
    return sum(1 for f in os.listdir(dossier) if f.lower().endswith(tuple(extensions)))

def verifier(source: str, destination: str, extensions: tuple[str, ...] | list[str] = EXTS_IMAGE) -> dict:
    ext_tuple = tuple(extensions)
    src_files = set(f for f in os.listdir(source) if f.lower().endswith(ext_tuple)) if os.path.exists(source) else set()
    dst_files = set(f for f in os.listdir(destination) if f.lower().endswith(ext_tuple)) if os.path.exists(destination) else set()

    return {
        "raw_count": len(src_files), 
        "upscale_count": len(dst_files),
        "verified": bool(src_files) and len(src_files) == len(dst_files), 
        "manquants": sorted(src_files - dst_files)
    }

def rapport_integrite(source: str, destination: str) -> dict:
    return verifier(source, destination)
