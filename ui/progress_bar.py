"""
ui/progress_bar.py — Barre de progression en ligne réécrite.
Utilisée pour upscale, extraction et autres opérations séquentielles longues.
"""
import sys
import time
from colorama import Fore, Style


class ProgressBar:
    """Barre de progression qui réécrit la même ligne console."""

    def __init__(self, total: int, label: str = "", width: int = 40):
        self.total = max(total, 1)
        self.label = label
        self.width = width
        self.current = 0
        self.start_time = time.time()

    def update(self, current: int, suffix: str = ""):
        self.current = current
        elapsed = time.time() - self.start_time
        pct = current / self.total
        filled = int(self.width * pct)
        bar = "█" * filled + "░" * (self.width - filled)
        elapsed_str = self._fmt_time(elapsed)

        line = (
            f"\r{Fore.CYAN}{self.label}{Style.RESET_ALL} "
            f"[{Fore.GREEN}{bar}{Style.RESET_ALL}] "
            f"{Fore.YELLOW}{current}/{self.total}{Style.RESET_ALL} "
            f"({pct:.0%}) {elapsed_str}"
        )
        if suffix:
            line += f" — {suffix}"

        sys.stdout.write(line)
        sys.stdout.flush()

    def done(self, msg: str = ""):
        elapsed = time.time() - self.start_time
        elapsed_str = self._fmt_time(elapsed)
        bar = "█" * self.width
        line = (
            f"\r{Fore.CYAN}{self.label}{Style.RESET_ALL} "
            f"[{Fore.GREEN}{bar}{Style.RESET_ALL}] "
            f"{Fore.GREEN}{self.total}/{self.total} ✔{Style.RESET_ALL} "
            f"{elapsed_str}"
        )
        if msg:
            line += f" — {msg}"
        sys.stdout.write(line + "\n")
        sys.stdout.flush()
        return elapsed

    @staticmethod
    def _fmt_time(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}h{m:02d}m{s:02d}s"
        return f"{m}m{s:02d}s"


def fmt_duration(seconds: float) -> str:
    return ProgressBar._fmt_time(seconds)
