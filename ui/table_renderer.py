"""
ui/table_renderer.py — Rendu de tableaux multi-colonnes alignés.
Export Markdown pour la vue d'avancement globale.
"""
import re
from colorama import Fore, Style

# Symboles d'état
SYMBOL_DONE    = f"{Fore.GREEN}✔{Style.RESET_ALL}"
SYMBOL_SKIP    = f"{Fore.YELLOW}–{Style.RESET_ALL}"
SYMBOL_UNKNOWN = f"{Fore.RED}?{Style.RESET_ALL}"


def status_cell(val) -> str:
    """Convertit une valeur de statut en cellule colorée."""
    if val is None:
        return SYMBOL_UNKNOWN
    if isinstance(val, bool):
        return SYMBOL_DONE if val else SYMBOL_SKIP
    if isinstance(val, str):
        if val == "termine":
            return f"{Fore.GREEN}✔ terminé{Style.RESET_ALL}"
        if val == "en_cours":
            return f"{Fore.YELLOW}▶ en cours{Style.RESET_ALL}"
        if val == "non_commence":
            return f"{Fore.WHITE}– non comm.{Style.RESET_ALL}"
        if val == "archive":
            return f"{Fore.CYAN}📦 archivé{Style.RESET_ALL}"
        return val
    if isinstance(val, (int, float)):
        pct = int(val * 100) if val <= 1.0 else int(val)
        if pct == 100:
            return f"{Fore.GREEN}{pct}%{Style.RESET_ALL}"
        if pct > 0:
            return f"{Fore.YELLOW}{pct}%{Style.RESET_ALL}"
        return f"{Fore.WHITE}{pct}%{Style.RESET_ALL}"
    return str(val)


def render_table(
    headers: list[str],
    rows: list[list],
    col_widths: list[int] | None = None,
) -> str:
    """
    Rend un tableau multi-colonnes aligné dans la console.
    Les cellules de statut connus sont colorées automatiquement.
    """
    STATUS_VALUES = {"termine", "en_cours", "non_commence", "archive", "?"}

    if col_widths is None:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    plain = _strip_ansi(str(cell))
                    col_widths[i] = max(col_widths[i], len(plain))

    sep = "─" * (sum(col_widths) + 3 * len(col_widths) + 1)
    lines = [f"{Fore.MAGENTA}{sep}{Style.RESET_ALL}"]

    # En-têtes
    header_line = "│ "
    for i, h in enumerate(headers):
        w = col_widths[i] if i < len(col_widths) else 10
        header_line += f"{Fore.CYAN}{Style.BRIGHT}{h:<{w}}{Style.RESET_ALL} │ "
    lines.append(header_line)
    lines.append(f"{Fore.MAGENTA}{sep}{Style.RESET_ALL}")

    # Lignes
    for row in rows:
        line = "│ "
        for i, cell in enumerate(row):
            w = col_widths[i] if i < len(col_widths) else 10
            is_status = (isinstance(cell, str) and cell in STATUS_VALUES) or \
                        isinstance(cell, bool) or cell is None or \
                        isinstance(cell, (int, float))
            cell_str = status_cell(cell) if is_status else str(cell)
            plain_len = len(_strip_ansi(cell_str))
            padding = " " * max(0, w - plain_len)
            line += f"{cell_str}{padding} │ "
        lines.append(line)

    lines.append(f"{Fore.MAGENTA}{sep}{Style.RESET_ALL}")
    return "\n".join(lines)


def export_markdown(
    titre: str,
    headers: list[str],
    rows: list[list],
    filename: str,
    extra_header_lines: list[str] | None = None,
) -> None:
    """
    Exporte un tableau au format Markdown.
    extra_header_lines : lignes insérées entre le titre et le tableau.
    """
    lines = [f"# {titre}", ""]
    if extra_header_lines:
        lines.extend(extra_header_lines)
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
    for row in rows:
        cells = [_markdown_status(c) for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _markdown_status(val) -> str:
    """Convertit un statut en texte Markdown lisible (sans ANSI)."""
    mapping = {
        "termine":       "✔ terminé",
        "en_cours":      "▶ en cours",
        "non_commence":  "– non comm.",
        "archive":       "📦 archivé",
        "?":             "?",
    }
    if isinstance(val, str) and val in mapping:
        return mapping[val]
    return _strip_ansi(str(val))


def _strip_ansi(text: str) -> str:
    """Supprime les codes ANSI d'une chaîne."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)
