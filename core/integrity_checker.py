"""
core/integrity_checker.py — Vérification d'intégrité source vs destination.
"""
import os

EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".psd"}


def count_images(path: str) -> int:
    if not os.path.isdir(path):
        return 0
    return sum(1 for f in os.listdir(path) if _is_image(f))


def list_images(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    return sorted([f for f in os.listdir(path) if _is_image(f)])


def check_integrity(source_path: str, dest_path: str) -> dict:
    src_images = set(list_images(source_path))
    dst_images = set(list_images(dest_path))
    src_stems = {os.path.splitext(f)[0] for f in src_images}
    dst_stems = {os.path.splitext(f)[0] for f in dst_images}
    missing_stems = src_stems - dst_stems
    return {
        "raw_count": len(src_images),
        "upscale_count": len(dst_images),
        "verified": len(missing_stems) == 0 and len(src_images) > 0,
        "missing": sorted(missing_stems),
    }


def _is_image(filename: str) -> bool:
    return os.path.splitext(filename.lower())[1] in EXTENSIONS_IMAGES
