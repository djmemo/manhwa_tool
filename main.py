"""
main.py — Point d'entrée principal de Manhwa Tool v2.
Flux interactif : sélection projet → alerte CBZ → sélection rôle → menu principal.
Mode batch : --batch --projet <nom> --role <dossier> --cmd <slug>
Mode watcher : --watch --projet <nom> --role <dossier>
"""
import os
import sys
import importlib
import pkgutil
import argparse
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from colorama import init as colorama_init
colorama_init(autoreset=True)

from config_loader import CFG, save_racine
from session import session
from ui.colors import title, info, warn, err, ok, separator, breadcrumb as fmt_bc
from ui.menu_engine import menu, pause, _clear
from core.project_manager import (
    scan_projects, create_project, read_project_yaml,
    detect_pending_cbz, recalculate_stats, get_next_chapter_number,
)
from core.role_manager import list_roles, create_role_yaml, ROLES_DISPONIBLES, read_role_yaml


BANNER = r"""
  __  __             _                    _____           _
 |  \/  |           | |                  |_   _|         | |
 | \  / | __ _ _ __ | |____      ____ _    | | ___   ___ | |
 | |\/| |/ _` | '_ \| '_ \ \ /\ / / _` |   | |/ _ \ / _ \| |
 | |  | | (_| | | | | | | \ V  V / (_| |   | | (_) | (_) | |
 |_|  |_|\__,_|_| |_|_| |_|\_/\_/ \__,_|   |_|\___/ \___/|_|
                                              v2.0 — OsirisScan
"""


def print_banner():
    _clear()
    print(title(BANNER))
    racine = session.racine_osirisscan or CFG.machine.racine_osirisscan or "?"
    print(info(f"  Racine : {racine}"))
    print(separator(CFG.console.largeur_banniere or 70))
    print()


# ── Sélection projet ───────────────────────────────────────────────────────────

def _prompt_racine(racine_actuelle: str = "") -> str:
    """
    Demande à l'utilisateur de saisir (ou modifier) racine_osirisscan.
    Boucle jusqu'à obtenir un chemin de dossier valide.
    Retourne le chemin validé.
    """
    while True:
        if racine_actuelle:
            print(info(f"  Racine actuelle : {racine_actuelle}"))
            print(info("  (Laisser vide pour conserver la valeur actuelle)"))
        else:
            print(warn("  ⚠  racine_osirisscan non configurée."))
            print(info("  Indiquez le chemin racine de vos projets OsirisScan."))
        print()
        print("  Nouveau chemin : ", end="", flush=True)
        raw = input().strip()

        # Conserver l'ancienne valeur si saisie vide et qu'une valeur existe
        if not raw and racine_actuelle:
            return racine_actuelle

        if not raw:
            print(err("  Le chemin ne peut pas être vide."))
            continue

        # Expansion ~ et variables d'environnement
        expanded = os.path.expandvars(os.path.expanduser(raw))

        if not os.path.isdir(expanded):
            print(err(f"  Dossier introuvable : {expanded}"))
            print(warn("  Vérifiez le chemin ou créez le dossier d'abord."))
            continue

        return expanded


def select_project() -> bool:
    """
    Sélection du projet actif.
    – Si racine_osirisscan n'est pas configurée → saisie forcée AVANT toute navigation.
    – Si elle est déjà définie   → accessible via l'option "Modifier la racine".
    """
    # ── Initialisation forcée si racine absente ───────────────────────────────
    racine = session.racine_osirisscan or CFG.machine.racine_osirisscan or ""
    if not racine or not os.path.isdir(racine):
        _clear()
        print(title(BANNER))
        print(separator(CFG.console.largeur_banniere or 70))
        print()
        if racine:
            print(err(f"  ✖  Racine configurée introuvable : {racine}"))
        racine = _prompt_racine(racine)
        save_racine(racine)
        print(ok(f"\n  ✔ Racine enregistrée : {racine}"))
        pause()

    session.racine_osirisscan = racine

    while True:
        print_banner()
        projects = scan_projects(racine)

        items = [p["nom"] for p in projects]
        items.append("➕  Créer un nouveau projet")
        items.append("🔧  Modifier la racine OsirisScan")
        items.append("❌  Quitter")

        idx = menu("Sélectionner un projet", items, breadcrumb=["OsirisScan"], allow_escape=False)
        if idx is None:
            return False

        # Quitter
        if idx == len(items) - 1:
            sys.exit(0)

        # Modifier la racine
        if idx == len(items) - 2:
            _clear()
            print(title(BANNER))
            print(separator(CFG.console.largeur_banniere or 70))
            print()
            new_racine = _prompt_racine(racine)
            if new_racine != racine:
                save_racine(new_racine)
                racine = new_racine
                session.racine_osirisscan = racine
                print(ok(f"\n  ✔ Racine mise à jour et sauvegardée : {racine}"))
            else:
                print(info("  Racine inchangée."))
            pause()
            continue

        # Créer un nouveau projet
        if idx == len(projects):
            _create_new_project(racine)
            continue

        proj = projects[idx]
        session.projet_chemin = proj["path"]
        session.projet_nom = proj["nom"]
        return True


def _create_new_project(racine: str):
    _clear()
    print(title("\n  ➕  Créer un nouveau projet\n"))
    print("  Nom de l'œuvre : ", end="", flush=True)
    name = input().strip()
    if not name:
        print(warn("  Nom vide, annulé."))
        pause()
        return

    role_idx = menu(
        "Choisir le rôle actif initial",
        [r["label"] for r in ROLES_DISPONIBLES],
        breadcrumb=["OsirisScan", "Nouveau projet"],
    )
    if role_idx is None:
        return

    roles = [ROLES_DISPONIBLES[role_idx]]
    path = create_project(racine, name, roles)
    print(ok(f"\n  ✔ Projet créé : {path}"))
    pause()


# ── Alerte CBZ ─────────────────────────────────────────────────────────────────

def alert_pending_cbz():
    cbz_list = detect_pending_cbz(session.projet_chemin)
    if cbz_list:
        _clear()
        print(warn(f"\n  📦  {len(cbz_list)} archive(s) CBZ en attente dans 00_Raw/\n"))
        for cbz in cbz_list[:10]:
            print(f"    • {cbz}")
        if len(cbz_list) > 10:
            print(f"    ... et {len(cbz_list) - 10} autre(s)")
        print()
        pause()


# ── Sélection rôle ─────────────────────────────────────────────────────────────

def select_role() -> bool:
    while True:
        print_banner()
        roles = list_roles(session.projet_chemin)

        items = [f"{r['label']}  ({r['dossier']})" for r in roles]
        items.append("➕  Initialiser un nouveau rôle")
        items.append("⬅  Changer de projet")

        bc = [session.projet_nom or "Projet"]
        idx = menu("Sélectionner le rôle actif", items, breadcrumb=["OsirisScan"] + bc)

        if idx is None or idx == len(items) - 1:
            session.reset_projet()
            return False

        if idx == len(roles):
            _init_new_role()
            continue

        role = roles[idx]
        session.role_dossier = role["dossier"]
        session.role_label = role["label"]
        return True


def _init_new_role():
    existing = {r["dossier"] for r in list_roles(session.projet_chemin)}
    available = [r for r in ROLES_DISPONIBLES if r["dossier"] not in existing]
    if not available:
        print(info("  Tous les rôles sont déjà initialisés."))
        pause()
        return
    idx = menu(
        "Choisir le rôle à initialiser",
        [f"{r['label']} ({r['dossier']})" for r in available],
        breadcrumb=session.breadcrumb(),
    )
    if idx is None:
        return
    role_info = available[idx]
    role_path = os.path.join(session.projet_chemin, role_info["dossier"])
    create_role_yaml(role_path, role_info["label"], role_info["dossier"])
    print(ok(f"\n  ✔ Rôle {role_info['label']} initialisé."))
    pause()


# ── Auto-découverte des commandes ──────────────────────────────────────────────

def load_commands() -> list[dict]:
    commands = []
    commands_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "commands")
    if not os.path.isdir(commands_dir):
        return commands

    for finder, module_name, _ in pkgutil.iter_modules([commands_dir]):
        if not module_name.startswith("cmd_"):
            continue
        try:
            mod = importlib.import_module(f"commands.{module_name}")
            commands.append({
                "module": module_name,
                "label": getattr(mod, "LABEL", module_name),
                "description": getattr(mod, "DESCRIPTION", ""),
                "run": getattr(mod, "run", None),
                "order": module_name,
            })
        except Exception as e:
            print(warn(f"  Commande ignorée ({module_name}): {e}"))

    commands.sort(key=lambda c: c["order"])
    return commands


def find_command_by_slug(slug: str) -> dict | None:
    """Trouve une commande par son slug (ex: 'extraction_cbz', '005', 'cmd_005')."""
    commands = load_commands()
    slug_lower = slug.lower().strip()
    for cmd in commands:
        mod = cmd["module"].lower()
        if (slug_lower in mod
                or mod.endswith(slug_lower)
                or slug_lower == mod.split("_", 2)[-1]):
            return cmd
    return None


# ── Menu principal ─────────────────────────────────────────────────────────────

def main_menu() -> str:
    commands = load_commands()

    while True:
        print_banner()
        recalculate_stats(session.projet_chemin)
        proj_data = read_project_yaml(session.projet_chemin)
        stats = proj_data.get("stats", {})
        prog = proj_data.get("progression", {})

        print(info(f"  Projet  : {session.projet_nom}"))
        print(info(f"  Rôle    : {session.role_label}  ({session.role_dossier})"))
        print(info(
            f"  Stats   : {stats.get('chapitres_termines', 0)} terminé(s) | "
            f"{stats.get('chapitres_en_cours', 0)} en cours | "
            f"prochain ch.{prog.get('prochain_chapitre', 1)} | "
            f"upscale cumulé : {stats.get('temps_total_upscale', '0:00:00')}"
        ))
        print()

        items = [c["label"] for c in commands]
        items.append("⬅  Changer de rôle")
        items.append("🏠  Changer de projet")
        items.append("❌  Quitter")

        idx = menu("Menu principal", items, breadcrumb=session.breadcrumb(), allow_escape=False)
        if idx is None:
            continue

        if idx == len(items) - 1:
            sys.exit(0)
        if idx == len(items) - 2:
            session.reset_projet()
            return "change_projet"
        if idx == len(items) - 3:
            session.reset_role()
            return "change_role"

        cmd = commands[idx]
        if cmd["run"] is None:
            print(warn("  Cette commande n'est pas encore disponible."))
            pause()
            continue
        try:
            cmd["run"]()
        except KeyboardInterrupt:
            print(warn("\n  Opération interrompue."))
            pause()
        except Exception as e:
            print(err(f"\n  Erreur : {e}"))
            import traceback; traceback.print_exc()
            pause()


# ── Mode Watcher ───────────────────────────────────────────────────────────────

def run_watcher_mode(projet_chemin: str, projet_nom: str, role_dossier: str):
    """
    Surveille 00_Raw/ du projet et affiche une notification console
    à chaque nouveau CBZ détecté. Arrêt propre avec Ctrl+C.
    Implémente l'étape 6 : surveillance réactive sans interaction.
    """
    from core.watcher import RawWatcher

    raw_path = os.path.join(projet_chemin, "00_Raw")
    if not os.path.isdir(raw_path):
        print(err(f"  Dossier 00_Raw/ introuvable : {raw_path}"))
        sys.exit(1)

    detected: list[str] = []
    lock = threading.Lock()

    def on_new_cbz(filename: str):
        ts = time.strftime("%H:%M:%S")
        with lock:
            detected.append(filename)
            print(warn(f"\n  [{ts}]  📦  Nouveau CBZ détecté : {filename}"))
            print(info(f"  Total en attente : {len(detected)}"))
            print(info(f"  Lancez : run.bat --batch --projet \"{projet_nom}\" "
                       f"--role {role_dossier} --cmd extraction_cbz"))

    watcher = RawWatcher(raw_path, on_new_cbz)
    watcher.start()

    print(ok(f"\n  🔍  Surveillance active : {raw_path}"))
    print(info(f"  Projet : {projet_nom}  |  Rôle : {role_dossier}"))
    print(info("  Appuyez sur Ctrl+C pour arrêter.\n"))

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        print(info(f"\n  Surveillance arrêtée. {len(detected)} CBZ détecté(s) au total."))


# ── Mode Batch ─────────────────────────────────────────────────────────────────

def run_batch_mode(args: argparse.Namespace) -> int:
    """
    Exécute une commande unique sans interaction.
    Usage : --batch --projet <nom_ou_chemin> --role <dossier> --cmd <slug>
    Retourne le code de sortie (0 = succès).
    """
    racine = args.config_racine or CFG.machine.racine_osirisscan or ""
    session.racine_osirisscan = racine

    # Résoudre le projet
    if not args.projet:
        print(err("  --batch requiert --projet <nom>"))
        return 1

    projects = scan_projects(racine)
    projet = None
    for p in projects:
        if args.projet.lower() in (p["nom"].lower(), p["dossier"].lower(), p["path"].lower()):
            projet = p
            break

    if projet is None:
        print(err(f"  Projet introuvable : {args.projet}"))
        print(info(f"  Projets disponibles : {[p['nom'] for p in projects]}"))
        return 1

    session.projet_chemin = projet["path"]
    session.projet_nom = projet["nom"]

    # Résoudre le rôle
    if not args.role:
        print(err("  --batch requiert --role <dossier>  (ex: 01_Clean)"))
        return 1

    roles = list_roles(session.projet_chemin)
    role = None
    for r in roles:
        if args.role.lower() in (r["dossier"].lower(), r["label"].lower()):
            role = r
            break

    if role is None:
        print(err(f"  Rôle introuvable : {args.role}"))
        print(info(f"  Rôles disponibles : {[r['dossier'] for r in roles]}"))
        return 1

    session.role_dossier = role["dossier"]
    session.role_label = role["label"]

    # Résoudre la commande
    if not args.cmd:
        print(err("  --batch requiert --cmd <slug>  (ex: extraction_cbz, 005, pipeline_complet)"))
        return 1

    cmd = find_command_by_slug(args.cmd)
    if cmd is None or cmd["run"] is None:
        print(err(f"  Commande introuvable : {args.cmd}"))
        cmds = load_commands()
        print(info(f"  Commandes disponibles : {[c['module'] for c in cmds]}"))
        return 1

    print(ok(f"\n  [BATCH] {cmd['label']}"))
    print(info(f"  Projet : {session.projet_nom}  |  Rôle : {session.role_label}\n"))

    try:
        cmd["run"]()
        return 0
    except Exception as e:
        print(err(f"\n  Erreur batch : {e}"))
        import traceback; traceback.print_exc()
        return 1


# ── Point d'entrée ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Manhwa Tool v2 — Gestion de workflow scanlation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  Mode interactif (défaut) :
    python main.py

  Mode batch (sans interaction) :
    python main.py --batch --projet "Mon Manhwa" --role 01_Clean --cmd extraction_cbz
    python main.py --batch --projet "Mon Manhwa" --role 01_Clean --cmd upscale_realesrgan

  Mode watcher (surveillance réactive) :
    python main.py --watch --projet "Mon Manhwa" --role 01_Clean

  Config personnalisée :
    python main.py --config /chemin/vers/config.yaml
        """,
    )
    parser.add_argument("--batch", action="store_true",
                        help="Mode batch : exécute --cmd sans interaction")
    parser.add_argument("--watch", action="store_true",
                        help="Mode watcher : surveille 00_Raw/ en continu")
    parser.add_argument("--projet", metavar="NOM",
                        help="Nom ou chemin du projet (requis en mode --batch/--watch)")
    parser.add_argument("--role", metavar="DOSSIER",
                        help="Dossier du rôle actif (ex: 01_Clean)")
    parser.add_argument("--cmd", metavar="SLUG",
                        help="Commande à exécuter (ex: extraction_cbz, 005, pipeline_complet)")
    parser.add_argument("--config", metavar="FICHIER",
                        help="Chemin vers un config.yaml alternatif")
    args = parser.parse_args()

    # Recharger config si --config fourni
    args.config_racine = None
    if args.config:
        if not os.path.isfile(args.config):
            print(err(f"  config.yaml introuvable : {args.config}"))
            sys.exit(1)
        from config_loader import load_config
        import config_loader
        config_loader.CFG = load_config(args.config)
        # Lire la racine depuis la config alternative
        args.config_racine = config_loader.CFG.machine.racine_osirisscan

    # ── Mode watcher ──────────────────────────────────────────────────────────
    if args.watch:
        racine = args.config_racine or CFG.machine.racine_osirisscan or ""
        if not args.projet:
            print(err("  --watch requiert --projet <nom>"))
            sys.exit(1)
        projects = scan_projects(racine)
        projet = next(
            (p for p in projects
             if args.projet.lower() in (p["nom"].lower(), p["dossier"].lower())),
            None
        )
        if projet is None:
            print(err(f"  Projet introuvable : {args.projet}"))
            sys.exit(1)
        role_dossier = args.role or "01_Clean"
        run_watcher_mode(projet["path"], projet["nom"], role_dossier)
        sys.exit(0)

    # ── Mode batch ────────────────────────────────────────────────────────────
    if args.batch:
        code = run_batch_mode(args)
        sys.exit(code)

    # ── Mode interactif (défaut) ──────────────────────────────────────────────
    state = "select_project"
    while True:
        if state == "select_project":
            if not select_project():
                break
            state = "alert_cbz"

        elif state == "alert_cbz":
            alert_pending_cbz()
            state = "select_role"

        elif state == "select_role":
            if not select_role():
                state = "select_project"
                continue
            state = "main_menu"

        elif state == "main_menu":
            result = main_menu()
            if result == "change_projet":
                state = "select_project"
            elif result == "change_role":
                state = "select_role"
            else:
                break


if __name__ == "__main__":
    main()
