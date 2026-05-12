"""
cmd_008_parametres.py — Paramètres du projet et du rôle.
Gestion membres, modèle ESRGAN, qscale, sous-dossiers (CRUD), changelog complet.
"""
import os
from session import session
from core.role_manager import (
    read_role_yaml, write_role_yaml, update_field,
    add_membre, remove_membre,
)
from core.changelog import read_changelog
from core.project_manager import read_project_yaml
from ui.colors import title, info, ok, warn, err, separator
from ui.menu_engine import menu, prompt_text, prompt_int, pause, _clear

LABEL = "⚙️   Paramètres"
DESCRIPTION = "Rôle, membres, modèle ESRGAN, qscale, sous-dossiers, changelog"

MODELS = [
    "realesrgan-x4plus-anime",
    "realesrgan-x4plus",
    "realesr-animevideov3",
    "realesrnet-x4plus",
]


def run():
    while True:
        _clear()
        role_path = os.path.join(session.projet_chemin, session.role_dossier)
        role_data = read_role_yaml(role_path) or {}
        current_model = role_data.get("config", {}).get("model_esrgan", "?")
        qscale_g = role_data.get("config", {}).get("qscale_global", 95)
        qscale_gr = role_data.get("config", {}).get("qscale_groupe", 92)
        membres = role_data.get("role", {}).get("membres", [])

        print(title(f"\n  ⚙️   Paramètres — {session.projet_nom} / {session.role_label}\n"))
        print(info(f"  Modèle ESRGAN   : {current_model}"))
        print(info(f"  Qualité globale : {qscale_g}  |  Qualité groupe : {qscale_gr}"))
        print(info(f"  Membres         : {', '.join(membres) if membres else '(aucun)'}"))
        print()

        items = [
            "📋  Voir le changelog complet",
            "🤖  Changer le modèle Real-ESRGAN",
            "🎚️   Modifier les qualités JPEG (qscale)",
            "👥  Gérer les membres du rôle",
            "📁  Gérer les sous-dossiers du chapitre",
            "ℹ️   Infos projet",
            "⬅  Retour au menu",
        ]
        idx = menu("Paramètres", items, breadcrumb=session.breadcrumb())
        if idx is None or idx == len(items) - 1:
            return

        actions = [
            _show_changelog,
            lambda: _change_model(role_path, current_model),
            lambda: _change_qscale(role_path, role_data),
            lambda: _manage_membres(role_path),
            lambda: _manage_sous_dossiers(role_path, role_data),
            _show_project_info,
        ]
        actions[idx]()


# ── Changelog ─────────────────────────────────────────────────────────────────

def _show_changelog():
    _clear()
    project_yaml = os.path.join(session.projet_chemin, ".project.yaml")
    entries = read_changelog(project_yaml)
    print(title(f"\n  📋  Changelog — {session.projet_nom}\n"))
    print(separator(70))
    if not entries:
        print(info("  Aucune entrée dans le changelog."))
    else:
        for e in entries:
            date = e.get("date", "")
            role = e.get("role", "")
            action = e.get("action", "")
            print(f"  {date}  [{role}]  {action}")
    print(separator(70))
    print(info(f"\n  Total : {len(entries)} entrée(s)"))
    pause()


# ── Modèle ESRGAN ─────────────────────────────────────────────────────────────

def _change_model(role_path: str, current: str):
    _clear()
    print(info(f"  Modèle actuel : {current}\n"))
    idx = menu("Choisir le nouveau modèle", MODELS, breadcrumb=session.breadcrumb())
    if idx is not None:
        update_field(role_path, "config", "model_esrgan", MODELS[idx])
        print(ok(f"\n  ✔ Modèle mis à jour : {MODELS[idx]}"))
        pause()


# ── QScale ────────────────────────────────────────────────────────────────────

def _change_qscale(role_path: str, role_data: dict):
    _clear()
    cfg = role_data.get("config", {})
    print(title("\n  🎚️   Qualités JPEG\n"))
    print(info(f"  qscale_global  (fusion globale)  : {cfg.get('qscale_global', 95)}"))
    print(info(f"  qscale_groupe  (fusion par groupe): {cfg.get('qscale_groupe', 92)}\n"))

    items = ["Modifier qscale_global", "Modifier qscale_groupe", "⬅  Retour"]
    idx = menu("Qscale", items, breadcrumb=session.breadcrumb())
    if idx is None or idx == 2:
        return

    field = "qscale_global" if idx == 0 else "qscale_groupe"
    default = cfg.get(field, 95 if idx == 0 else 92)
    val = prompt_int(f"  Nouvelle valeur (1-100, actuelle {default})", default=default)
    val = max(1, min(100, val))
    update_field(role_path, "config", field, val)
    print(ok(f"\n  ✔ {field} = {val}"))
    pause()


# ── Membres ───────────────────────────────────────────────────────────────────

def _manage_membres(role_path: str):
    while True:
        _clear()
        role_data = read_role_yaml(role_path) or {}
        membres = role_data.get("role", {}).get("membres", [])
        print(title(f"\n  👥  Membres — {session.role_label}\n"))

        items = membres + ["➕  Ajouter un membre", "⬅  Retour"]
        idx = menu("Membres", items, breadcrumb=session.breadcrumb())
        if idx is None or idx == len(items) - 1:
            return

        if idx == len(membres):
            nom = prompt_text("  Nom du nouveau membre")
            if nom:
                add_membre(role_path, nom)
                print(ok(f"  ✔ {nom} ajouté."))
                pause()
        else:
            nom = membres[idx]
            items2 = [f"🗑  Supprimer '{nom}'", "⬅  Retour"]
            choice = menu(f"Membre : {nom}", items2, breadcrumb=session.breadcrumb())
            if choice == 0:
                remove_membre(role_path, nom)
                print(ok(f"  ✔ {nom} supprimé."))
                pause()


# ── Sous-dossiers CRUD ────────────────────────────────────────────────────────

def _manage_sous_dossiers(role_path: str, role_data: dict):
    """
    Affiche et permet d'ajouter/supprimer des sous-dossiers dans .role.yaml.
    Attention : ne crée/supprime PAS les dossiers physiques existants.
    """
    while True:
        _clear()
        role_data = read_role_yaml(role_path) or {}
        sous_dossiers = role_data.get("sous_dossiers", [])
        print(title(f"\n  📁  Sous-dossiers — {session.role_label}\n"))

        noms = [sd.get("nom", sd) if isinstance(sd, dict) else sd for sd in sous_dossiers]
        items = noms + ["➕  Ajouter un sous-dossier", "⬅  Retour"]
        idx = menu("Sous-dossiers", items, breadcrumb=session.breadcrumb())

        if idx is None or idx == len(items) - 1:
            return

        if idx == len(noms):
            # Ajouter
            nom = prompt_text("  Nom du sous-dossier (ex: 05_Archive)")
            if nom:
                role_data = read_role_yaml(role_path) or {}
                sds = role_data.setdefault("sous_dossiers", [])
                existing_noms = [s.get("nom", s) if isinstance(s, dict) else s for s in sds]
                if nom in existing_noms:
                    print(warn(f"  '{nom}' existe déjà."))
                else:
                    sds.append({"nom": nom, "index": len(sds)})
                    write_role_yaml(role_path, role_data)
                    print(ok(f"  ✔ Sous-dossier '{nom}' ajouté à .role.yaml"))
                    print(warn("  Note : le dossier physique n'est pas créé automatiquement."))
                pause()
        else:
            # Supprimer
            nom_sd = noms[idx]
            items2 = [f"🗑  Supprimer '{nom_sd}' de la config", "⬅  Retour"]
            choice = menu(f"Sous-dossier : {nom_sd}", items2, breadcrumb=session.breadcrumb())
            if choice == 0:
                role_data = read_role_yaml(role_path) or {}
                sds = role_data.get("sous_dossiers", [])
                role_data["sous_dossiers"] = [
                    s for s in sds
                    if (s.get("nom", s) if isinstance(s, dict) else s) != nom_sd
                ]
                write_role_yaml(role_path, role_data)
                print(ok(f"  ✔ '{nom_sd}' supprimé de la config."))
                print(warn("  Note : le dossier physique n'est pas supprimé."))
                pause()


# ── Infos projet ──────────────────────────────────────────────────────────────

def _show_project_info():
    _clear()
    data = read_project_yaml(session.projet_chemin)
    proj = data.get("project", {})
    stats = data.get("stats", {})
    prog = data.get("progression", {})
    roles = data.get("roles_declares", [])

    print(title(f"\n  ℹ️   Infos projet — {session.projet_nom}\n"))
    print(separator(60))
    print(info(f"  Nom             : {proj.get('name', '?')}"))
    print(info(f"  Créé le         : {proj.get('created_at', '?')}"))
    print(info(f"  Racine          : {proj.get('racine_osirisscan', '?')}"))
    print(info(f"  Chemin          : {session.projet_chemin}"))
    print(separator(60))
    print(info(f"  Terminés        : {stats.get('chapitres_termines', 0)}"))
    print(info(f"  En cours        : {stats.get('chapitres_en_cours', 0)}"))
    print(info(f"  Dernier terminé : ch.{prog.get('dernier_chapitre_termine', 0)}"))
    print(info(f"  Prochain        : ch.{prog.get('prochain_chapitre', 1)}"))
    print(info(f"  Temps upscale   : {stats.get('temps_total_upscale', '0:00:00')}"))
    print(info(f"  Dernière activ. : {stats.get('derniere_activite', '?')}"))
    print(separator(60))
    print(info(f"  Rôles déclarés  :"))
    for r in roles:
        print(f"    • {r.get('label', '?')}  ({r.get('dossier', '?')})")
    pause()
