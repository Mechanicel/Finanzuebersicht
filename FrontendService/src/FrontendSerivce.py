import logging

import customtkinter

from src.logging_config import configure_logging
from src.navigator import Navigator

logger = logging.getLogger(__name__)


def create_app() -> customtkinter.CTk:
    customtkinter.set_appearance_mode("System")
    customtkinter.set_default_color_theme("blue")

    app = customtkinter.CTk()
    app.geometry("1100x780")
    app.minsize(980, 680)
    app.title("Finanzübersicht")

    # Stabiler Maximized-Start: manche Umgebungen setzen nach dem ersten Zeichnen
    # den gespeicherten Geometry-Wert erneut zurück.
    def _apply_zoomed(*_):
        try:
            app.state("zoomed")
            return
        except Exception:
            pass
        try:
            app.attributes("-zoomed", True)
            return
        except Exception:
            app.attributes("-fullscreen", True)

    _apply_zoomed()
    app.after_idle(_apply_zoomed)
    app.after(250, _apply_zoomed)
    return app


def run() -> None:
    configure_logging()
    logger.info("App-Start: Initialisierung beginnt")

    app = create_app()
    navigator = Navigator(app)
    navigator.navigate("MainScreen")

    def close_app():
        logger.info("App-Start: Anwendung wird beendet")
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", close_app)
    logger.info("App-Start: Initialisierung abgeschlossen, starte mainloop")
    app.mainloop()


if __name__ == "__main__":
    run()
