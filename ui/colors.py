"""
ui/colors.py — Palette console et helpers d'affichage coloré.
Encapsule colorama pour un usage cohérent dans toute l'application.
"""
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)


def ok(msg: str) -> str:
    """Succès — vert."""
    return f"{Fore.GREEN}✔ {msg}{Style.RESET_ALL}"


def err(msg: str) -> str:
    """Erreur — rouge (actions destructrices incluses)."""
    return f"{Fore.RED}✖ {msg}{Style.RESET_ALL}"


def warn(msg: str) -> str:
    """Avertissement — jaune."""
    return f"{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}"


def info(msg: str) -> str:
    """Information neutre — cyan."""
    return f"{Fore.CYAN}ℹ {msg}{Style.RESET_ALL}"


def title(msg: str) -> str:
    """Titre et séparateurs — magenta."""
    return f"{Fore.MAGENTA}{Style.BRIGHT}{msg}{Style.RESET_ALL}"


def muted(msg: str) -> str:
    """Texte atténué — gris."""
    return f"{Style.DIM}{msg}{Style.RESET_ALL}"


def highlight(msg: str) -> str:
    """Mise en valeur — blanc gras."""
    return f"{Style.BRIGHT}{msg}{Style.RESET_ALL}"


def confirm_danger(prompt: str) -> bool:
    """Demande une confirmation rouge pour une action irréversible.
    Retourne True uniquement si l'utilisateur tape 'oui' exactement."""
    print(f"{Fore.RED}{Style.BRIGHT}⚠  ACTION IRRÉVERSIBLE{Style.RESET_ALL}")
    print(f"{Fore.RED}{prompt}{Style.RESET_ALL}")
    print(f"{Fore.RED}Tapez 'oui' pour confirmer : {Style.RESET_ALL}", end="", flush=True)
    response = input().strip().lower()
    return response == "oui"


def separator(width: int = 60, char: str = "─") -> str:
    """Ligne de séparation magenta."""
    return f"{Fore.MAGENTA}{char * width}{Style.RESET_ALL}"


def breadcrumb(parts: list[str]) -> str:
    """Affiche le fil d'Ariane."""
    joined = " > ".join(parts)
    return f"{Fore.CYAN}{Style.DIM}{joined}{Style.RESET_ALL}"
