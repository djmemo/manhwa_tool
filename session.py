"""
session.py — Contexte runtime partagé (source unique de vérité).
Toutes les commandes importent ce module pour accéder au contexte courant.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Session:
    """Contexte actif de l'application."""
    racine_osirisscan: str = ""
    projet_chemin: str = ""
    projet_nom: str = ""
    role_dossier: str = ""
    role_label: str = ""
    chapitre_actif: str = ""

    def is_projet_set(self) -> bool:
        return bool(self.projet_chemin and self.projet_nom)

    def is_role_set(self) -> bool:
        return bool(self.role_dossier and self.role_label)

    def is_chapitre_set(self) -> bool:
        return bool(self.chapitre_actif)

    def breadcrumb(self) -> list[str]:
        """Retourne le fil d'Ariane courant."""
        parts = ["OsirisScan"]
        if self.projet_nom:
            # Troncature si nom trop long
            nom = self.projet_nom if len(self.projet_nom) <= 30 else self.projet_nom[:27] + "..."
            parts.append(nom)
        if self.role_label:
            parts.append(self.role_label)
        if self.chapitre_actif:
            parts.append(self.chapitre_actif)
        return parts

    def reset_chapitre(self):
        self.chapitre_actif = ""

    def reset_role(self):
        self.role_dossier = ""
        self.role_label = ""
        self.chapitre_actif = ""

    def reset_projet(self):
        self.projet_chemin = ""
        self.projet_nom = ""
        self.role_dossier = ""
        self.role_label = ""
        self.chapitre_actif = ""


# Singleton global
session = Session()
