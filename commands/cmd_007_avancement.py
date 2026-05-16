"""
cmd_007 — Avancement
---------------------
Affiche un tableau multi-rôles / multi-chapitres avec l'état de chaque
étape (extraction, upscale, nettoyage, export, fusion).
Permet d'exporter le tableau en Markdown dans le dossier projet
sous la forme : NomOeuvre_avancement_YYYY-MM-DD.md
"""
import os
from datetime import datetime

LABEL = "Avancement"
DESCRIPTION = 'Affiche la progression multi-rôles et exporte un rapport Markdown'
def exporter_markdown(projet_chemin: str) -> str:
    from core import role_manager, status_manager

    nom_oeuvre = os.path.basename(projet_chemin.rstrip("/\\"))
    lignes = [
        f"# Avancement — {nom_oeuvre}\n",
        "| Chapitre | Rôle | Extraction | Upscale | Nettoyage | Export | Fusion | Statut |",
        "|---|---|---|---|---|---|---|---|"
    ]

    roles = role_manager.lister_roles(projet_chemin)
    for role in roles:
        role_dossier = role.get("dossier", "")
        role_label = role.get("label", "")
        rc = os.path.join(projet_chemin, role_dossier)
        if not os.path.isdir(rc):
            continue

        for ch in sorted(os.listdir(rc)):
            cc = os.path.join(rc, ch)
            if not os.path.isfile(os.path.join(cc, ".status.yaml")):
                continue

            st = status_manager.lire_status(cc)
            e = st.get("etapes", {})

            def cell(k): 
                return "✔" if e.get(k, {}).get("done") else "–"

            lignes.append(
                f"| {ch} | {role_label} | {cell('extraction_cbz')} | {cell('upscale')} | "
                f"{cell('nettoyage_psd')} | {cell('export_jpeg')} | {cell('fusion_finale')} | "
                f"{st.get('statut_global', '?')} |"
            )

    date_str = datetime.now().strftime("%Y-%m-%d")
    out_path = os.path.join(projet_chemin, f"{nom_oeuvre}_avancement_{date_str}.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")

    return out_path

def run(app=None):
    if app:
        from ui.screens.screen_avancement import AvancementScreen
        app.push_screen(AvancementScreen())
