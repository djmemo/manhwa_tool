from PIL import Image, ImageStat

def is_row_empty(img: Image.Image, y: int, tolerance: float = 2.0) -> bool:
    """
    Vérifie si une ligne horizontale de pixels est de couleur unie.
    tolerance permet d'accepter de légers artefacts JPEG (variance).
    """
    line = img.crop((0, y, img.width, y + 1))
    stat = ImageStat.Stat(line)
    # stddev (écart-type) très bas = pixels presque identiques = fond uni
    return all(s <= tolerance for s in stat.stddev)


def apply_watermark(
    img: Image.Image,
    watermark_path: str,
    opacity: float = 0.5,
    margin: int = 20,
    max_ratio: float = 0.25,
) -> Image.Image:
    """
    Ajoute un watermark en bas à droite sur une image.
    - opacity = 0.5 => transparence 50%
    - max_ratio = largeur max du watermark par rapport à l'image
    """
    if not watermark_path:
        return img

    LANCZOS = getattr(Image, "Resampling", Image).LANCZOS

    with Image.open(watermark_path).convert("RGBA") as wm:
        alpha = wm.getchannel("A").point(lambda p: int(p * opacity))
        wm.putalpha(alpha)

        max_wm_width = int(img.width * max_ratio)
        if max_wm_width > 0 and wm.width > max_wm_width:
            ratio = max_wm_width / wm.width
            new_size = (max_wm_width, int(wm.height * ratio))
            wm = wm.resize(new_size, LANCZOS)

        x = max(0, img.width - wm.width - margin)
        y = max(0, img.height - wm.height - margin)

        out = img.copy()
        out.paste(wm, (x, y), wm)
        return out


def slice_image(
    img: Image.Image,
    max_height: int,
    watermark_path: str | None = None,
    watermark_opacity: float = 0.5,
) -> tuple[list[Image.Image], int]:
    """
    Découpe une image géante en morceaux d'au maximum `max_height` pixels.
    Cherche intelligemment une gouttière pour éviter de couper du dessin.
    Retourne (liste_des_images, nombre_de_coupes_forcees).
    """
    slices = []
    current_y = 0
    # On cherche une gouttière jusqu'à 30% plus haut que la coupe max
    search_range = int(max_height * 0.3)
    forced_cuts = 0

    while current_y < img.height:
        if current_y + max_height >= img.height:
            # Reste de l'image plus petit que la hauteur max, on prend tout
            # slices.append(img.crop((0, current_y, img.width, img.height)))
            part = img.crop((0, current_y, img.width, img.height))
            if watermark_path:
                part = apply_watermark(part, watermark_path, opacity=watermark_opacity)
            slices.append(part)
            break

        target_y = current_y + max_height
        cut_y = target_y
        found_cut = False

        # Scanner de bas en haut depuis target_y pour trouver une zone unie
        for y in range(target_y, max(current_y, target_y - search_range), -1):
            if is_row_empty(img, y):
                cut_y = y
                found_cut = True
                break

        if not found_cut:
            forced_cuts += 1

        # slices.append(img.crop((0, current_y, img.width, cut_y)))
        part = img.crop((0, current_y, img.width, cut_y))
        if watermark_path:
            part = apply_watermark(part, watermark_path, opacity=watermark_opacity)
        slices.append(part)

        current_y = cut_y

    return slices, forced_cuts
