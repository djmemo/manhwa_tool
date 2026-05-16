PALETTE = {"ok": "#06d6a0", "err": "#ef233c", "warn": "#ffd166",
           "info": "#00b4d8", "title": "#e94560", "neutral": "#e0e0e0"}
def markup_ok(t): return f"[bold {PALETTE['ok']}]{t}[/]"
def markup_err(t): return f"[bold {PALETTE['err']}]{t}[/]"
def markup_warn(t): return f"[{PALETTE['warn']}]{t}[/]"
def markup_info(t): return f"[{PALETTE['info']}]{t}[/]"
def markup_title(t): return f"[bold {PALETTE['title']}]{t}[/]"
