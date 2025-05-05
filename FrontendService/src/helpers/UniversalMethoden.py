def clear_ui(app):
    """
    Entfernt alle Widgets aus dem übergebenen Fenster.

    :param app: Das Fenster (z.B. ein CustomTkinter-Objekt), dessen Widgets entfernt werden sollen.
    """
    for widget in app.winfo_children():
        widget.destroy()


def zentrieren(app):
    """
    Zentriert alle Grid-Spalten des übergebenen Widgets,
    indem die Spaltengewichte gleichmäßig verteilt werden.

    :param app: Das Widget (z.B. ein Frame oder Fenster), das zentriert werden soll.
    """
    cols = app.grid_size()[0]
    for i in range(cols):
        app.grid_columnconfigure(i, weight=1)


def schließen(app):
    """
    Schließt das übergebene Fenster.

    :param app: Das Fenster, das geschlossen werden soll.
    """
    app.destroy()

