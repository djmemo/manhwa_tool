"""
cmd_007_avancement.py — Vue d'avancement multi-rôles et multi-chapitres.
Export Markdown dans le dossier projet sous [nom]_avancement_[date].md.
"""
import os
from datetime import datetime
from session import session
from core.project_manager import list_chapters, read_project_yaml, recalculate_stats
from core.status_manager import read_status
from core.role_manager import list_roles
from ui.colors import title, info, ok, warn, separator
from ui.table_renderer import render_table, export_markdown, status_cell
from ui.menu_engine import pause, _clear, menu

LABEL = "📊  Vue d'avancement"
DESCRIPTION = "Tableau multi-rôles et multi-chapitres avec export Markdown"


def run():
    _clear()
    recalculate_stats(session.projet_chemin)
    roles = list_roles(session.projet_chemin)
    if not roles:
        print(warn("  Aucun rôle disponible."))
        pause()
        return

    # Collecter tous les chapitres uniques (union de tous les rôles)
    all_chapters: set[str] = set()
    for role in roles:
        for ch in list_chapters(role["path"]):
            all_chapters.add(ch)
    all_chapters_sorted = sorted(all_chapters)

    if not all_chapters_sorted:
        print(warn("  Aucun chapitre trouvé dans les rôles déclarés."))
        pause()
        return

    # Construire le tableau
    headers = ["Chapitre"] + [r["label"] for r in roles]
    rows = []
    for ch in all_chapters_sorted:
        row = [ch]
        for role in roles:
            ch_path = os.path.join(role["path"], ch)
            status = read_status(ch_path)
            if status is None:
                row.append("?")
            else:
                row.append(status.get("statut_global", "?"))
        rows.append(row)

    # Afficher les stats globales
    proj_data = read_project_yaml(session.projet_chemin)
    stats = proj_data.get("stats", {})
    prog = proj_data.get("progression", {})

    print(title(f"\n  📊  Avancement — {session.projet_nom}\n"))
    print(info(
        f"  Terminés : {stats.get('chapitres_termines', 0)}  |  "
        f"En cours : {stats.get('chapitres_en_cours', 0)}  |  "
        f"Total connus : {prog.get('chapitres_total_connus', 0)}  |  "
        f"Upscale cumulé : {stats.get('temps_total_upscale', '0:00:00')}"
    ))
    print(info(
        f"  Dernier terminé : ch.{prog.get('dernier_chapitre_termine', 0)}  |  "
        f"Prochain : ch.{prog.get('prochain_chapitre', 1)}  |  "
        f"Dernière activité : {stats.get('derniere_activite', '?')}"
    ))
    print()
    print(render_table(headers, rows))

    items = ["⬅  Retour", "📄  Exporter en Markdown"]
    idx = menu("", items, breadcrumb=session.breadcrumb())
    if idx == 1:
        _export_markdown(headers, rows, proj_data)


def _export_markdown(headers: list, rows: list, proj_data: dict):
    """Exporte le tableau dans le dossier du projet."""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    # Nom de fichier sûr
    safe_name = session.projet_nom.replace(" ", "_")
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-")[:40]
    filename = f"{safe_name}_avancement_{date_str}.md"

    # Export dans le dossier projet (à côté de .project.yaml)
    export_path = os.path.join(session.projet_chemin, filename)

    # Enrichir le markdown avec les stats
    stats = proj_data.get("stats", {})
    prog = proj_data.get("progression", {})
    extra_lines = [
        f"**Dernière activité** : {stats.get('derniere_activite', '?')}",
        f"**Chapitres terminés** : {stats.get('chapitres_termines', 0)} / {prog.get('chapitres_total_connus', 0)}",
        f"**Temps upscale cumulé** : {stats.get('temps_total_upscale', '0:00:00')}",
        f"**Prochain chapitre** : ch.{prog.get('prochain_chapitre', 1)}",
        "",
    ]

    export_markdown(
        titre=f"Avancement — {session.projet_nom}",
        headers=headers,
        rows=rows,
        filename=export_path,
        extra_header_lines=extra_lines,
    )
    print(ok(f"\n  ✔ Exporté : {export_path}"))
    pause()
