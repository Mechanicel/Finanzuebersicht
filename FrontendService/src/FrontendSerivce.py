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
    maximized_state = {"requested": False}

    def _is_maximized() -> bool:
        try:
            return str(app.state()).lower() == "zoomed"
        except Exception:
            return False

    def _apply_zoomed(*_):
        if _is_maximized():
            maximized_state["requested"] = True
            return
        try:
            app.state("zoomed")
            maximized_state["requested"] = True
            return
        except Exception:
            pass
        try:
            app.attributes("-zoomed", True)
            maximized_state["requested"] = True
            return
        except Exception:
            # Fallback bewusst vermeiden: Fullscreen kann bei manchen WM zu
            # späteren State-Resets führen. Dann lieber normal maximieren lassen.
            logger.debug("Maximierter Start über WM nicht verfügbar.")

    _apply_zoomed()
    app.after_idle(_apply_zoomed)
    app.after(250, _apply_zoomed)
    app.after(800, _apply_zoomed)

    def _guard_window_state(_event=None):
        if maximized_state["requested"] and _is_maximized():
            return
        _apply_zoomed()

    app.bind("<Map>", _guard_window_state, add="+")
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
