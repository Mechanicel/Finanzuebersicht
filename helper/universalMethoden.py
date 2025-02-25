# universalMethoden.py
def zentrieren(widget):
    """Zentriert alle Grid-Spalten des Widgets."""
    for i in range(widget.grid_size()[0]):
        widget.grid_columnconfigure(i, weight=1)

def clear_ui(app):
    """Entfernt alle Widgets aus dem übergebenen Fenster."""
    for widget in app.winfo_children():
        widget.destroy()

def schließen(app):
    app.destroy()
