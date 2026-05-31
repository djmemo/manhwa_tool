import os
from core.utils import EXTS_IMAGE, lister_images

def compter_images(dossier: str, extensions: tuple[str, ...] | list[str] = EXTS_IMAGE) -> int:
    if not os.path.exists(dossier):
        return 0
    return len(lister_images(dossier, tuple(extensions)))

def verifier(source: str, destination: str, extensions: tuple[str, ...] | list[str] = EXTS_IMAGE) -> dict:
    ext_tuple = tuple(extensions)
    src_files = set(lister_images(source, ext_tuple)) if os.path.exists(source) else set()
    dst_files = set(lister_images(destination, ext_tuple)) if os.path.exists(destination) else set()

    return {
        "raw_count": len(src_files),
        "upscale_count": len(dst_files),
        "verified": bool(src_files) and len(src_files) == len(dst_files),
        "manquants": sorted([os.path.basename(f) for f in (src_files - dst_files)])
    }

def rapport_integrite(source: str, destination: str) -> dict:
    return verifier(source, destination)
