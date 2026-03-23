from flask import Flask

from src.api.stock import stock_bp
from src.utils.config import MARKETDATA_HOST, MARKETDATA_PORT
from src.utils.logger import logger


def create_app() -> Flask:
    """
    Factory-Funktion für Flask-Anwendung.
    Registriert alle Blueprints und konfiguriert Logging.
    """
    app = Flask(__name__)
    app.register_blueprint(stock_bp)

    logger.info("Flask-Anwendung initialisiert und Stock-Blueprint registriert")
    return app


def main() -> int:
    app = create_app()
    logger.info("Starte Flask-Server auf http://%s:%s", MARKETDATA_HOST, MARKETDATA_PORT)
    app.run(host=MARKETDATA_HOST, port=MARKETDATA_PORT, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
