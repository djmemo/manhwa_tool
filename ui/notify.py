def notify_ok(app, msg: str): app.notify(msg, severity="information", timeout=3)
def notify_err(app, msg: str): app.notify(msg, severity="error", timeout=5)
def notify_warn(app, msg: str): app.notify(msg, severity="warning", timeout=4)
