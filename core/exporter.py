import os
import zipfile
from PIL import Image

def exporter_multi_cibles(
    slices: list[Image.Image], 
    dest_dir: str, 
    chapter_name: str, 
    png: bool = True, 
    jpeg: bool = True, 
    cbz: bool = True,
    jpeg_quality: int = 95
) -> dict:

    os.makedirs(dest_dir, exist_ok=True)
    paths_created = []

    png_dir = os.path.join(dest_dir, "Webtoon_Slices_PNG")
    jpeg_dir = os.path.join(dest_dir, "Webtoon_Slices_JPEG")

    if png: os.makedirs(png_dir, exist_ok=True)
    if jpeg: os.makedirs(jpeg_dir, exist_ok=True)

    # 1. Sauvegarde des images
    for i, img in enumerate(slices):
        filename = f"{chapter_name}_slice_{i+1:03d}"
        if png:
            p = os.path.join(png_dir, f"{filename}.png")
            img.save(p, "PNG")
            paths_created.append(p)
        if jpeg:
            p = os.path.join(jpeg_dir, f"{filename}.jpg")
            img.save(p, "JPEG", quality=jpeg_quality)
            paths_created.append(p)

    # 2. Création de l'archive CBZ
    cbz_path = None
    if cbz:
        cbz_path = os.path.join(dest_dir, f"{chapter_name}_Release.cbz")
        # On préfère mettre les JPEGs dans le CBZ pour limiter le poids
        source_dir = jpeg_dir if jpeg else (png_dir if png else None)

        if source_dir and os.path.exists(source_dir):
            with zipfile.ZipFile(cbz_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(os.listdir(source_dir)):
                    zf.write(os.path.join(source_dir, f), f)
            paths_created.append(cbz_path)

    return {
        "slices_count": len(slices),
        "files_created": len(paths_created),
        "cbz_path": cbz_path
    }
