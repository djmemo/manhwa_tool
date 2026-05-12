"""
ui/menu_engine.py — Navigation clavier via readchar.
Interface: menu(titre, items, breadcrumb) -> int | None
"""
import sys
import os
import readchar
from ui.colors import title, muted, separator, breadcrumb as fmt_breadcrumb, info

# Gestion de la touche Escape (peut ne pas exister sur tous les OS)
_ESCAPE_KEY = getattr(readchar.key, 'ESCAPE', '\x1b')


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def menu(
    titre: str,
    items: list[str],
    breadcrumb: list[str] | None = None,
    allow_escape: bool = True,
    width: int = 60,
) -> int | None:
    """
    Affiche un menu interactif avec navigation clavier.

    Args:
        titre: Titre du menu.
        items: Liste des options à afficher.
        breadcrumb: Fil d'Ariane (liste de strings).
        allow_escape: Autoriser Échap pour remonter (retourne None).
        width: Largeur de la bannière.

    Returns:
        Index de l'item sélectionné (0-based), ou None si Échap.
    """
    if not items:
        print(info("Aucun élément à afficher."))
        input("Appuyez sur Entrée pour continuer...")
        return None

    cursor = 0

    while True:
        _clear()

        # Fil d'Ariane
        if breadcrumb:
            print(fmt_breadcrumb(breadcrumb))
            print()

        # Titre
        print(separator(width))
        print(title(f"  {titre}"))
        print(separator(width))
        print()

        # Items
        for i, item in enumerate(items):
            if i == cursor:
                print(f"  {title('▶')}  {item}")
            else:
                print(f"     {muted(item)}")

        print()
        if allow_escape:
            print(muted("  ↑↓ Naviguer  |  Entrée Sélectionner  |  Échap Retour"))
        else:
            print(muted("  ↑↓ Naviguer  |  Entrée Sélectionner"))

        # Lecture clavier
        key = readchar.readkey()

        if key == readchar.key.UP:
            cursor = (cursor - 1) % len(items)
        elif key == readchar.key.DOWN:
            cursor = (cursor + 1) % len(items)
        elif key == readchar.key.ENTER:
            return cursor
        elif key == _ESCAPE_KEY and allow_escape:
            return None


def prompt_text(label: str, default: str = "") -> str:
    """Saisie texte simple avec valeur par défaut."""
    if default:
        print(f"{label} [{default}]: ", end="", flush=True)
        value = input().strip()
        return value if value else default
    else:
        print(f"{label}: ", end="", flush=True)
        return input().strip()


def prompt_int(label: str, default: int | None = None, min_val: int = 1) -> int:
    """Saisie entière avec validation."""
    while True:
        if default is not None:
            print(f"{label} [{default}]: ", end="", flush=True)
            raw = input().strip()
            if not raw:
                return default
        else:
            print(f"{label}: ", end="", flush=True)
            raw = input().strip()

        try:
            val = int(raw)
            if val >= min_val:
                return val
            print(f"  Valeur minimale : {min_val}")
        except ValueError:
            print("  Entier attendu.")


def pause(msg: str = "Appuyez sur Entrée pour continuer..."):
    """Pause interactive."""
    input(f"\n{muted(msg)}")
