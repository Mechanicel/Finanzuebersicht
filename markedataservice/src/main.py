from flask import Flask

from markedataservice.src.api.stock import stock_bp
from markedataservice.src.utils.logger import logger


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
    logger.info("Starte Flask-Server auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
