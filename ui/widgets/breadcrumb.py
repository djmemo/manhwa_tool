from textual.widget import Widget
from textual.reactive import reactive
from session import SESSION
class Breadcrumb(Widget):
    text: str = reactive("")
    def on_mount(self): self.text = SESSION.breadcrumb()
    def render(self): return f" 📂 {self.text}"
    def refresh_breadcrumb(self): self.text = SESSION.breadcrumb()
