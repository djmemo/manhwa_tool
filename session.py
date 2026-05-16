class _Session:
    def __init__(self):
        self.racine_scantrad: str = ""
        self.projet_chemin: str = ""
        self.projet_nom: str = ""
        self.role_dossier: str = ""
        self.role_label: str = ""
        self.chapitre_actif: str = ""
    def reset(self): self.__init__()
    def breadcrumb(self) -> str:
        parts = ["OsirisScan"]
        if self.projet_nom: parts.append(self.projet_nom)
        if self.role_label: parts.append(self.role_label)
        if self.chapitre_actif: parts.append(self.chapitre_actif)
        return " > ".join(parts)

SESSION = _Session()
