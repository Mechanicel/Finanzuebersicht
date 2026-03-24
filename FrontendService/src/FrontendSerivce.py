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
    return app


def run() -> None:
    configure_logging(logging.DEBUG)
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
