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

def slice_image(img: Image.Image, max_height: int) -> tuple[list[Image.Image], int]:
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
            slices.append(img.crop((0, current_y, img.width, img.height)))
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

        slices.append(img.crop((0, current_y, img.width, cut_y)))
        current_y = cut_y

    return slices, forced_cuts
