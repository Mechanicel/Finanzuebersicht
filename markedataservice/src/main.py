from flask import Flask

from api.stock import stock_bp
from markedataservice.src.utils.logger import logger


def create_app() -> Flask:
    """
    Factory-Funktion für Flask-Anwendung.
    Registriert alle Blueprints und konfiguriert Logging.
    """
    app = Flask(__name__)
    # Weitere Konfiguration hier laden, z.B. aus Umgebungsvariablen

    # Registriere Stock-Blueprint
    app.register_blueprint(stock_bp)

    logger.info("Flask-Anwendung initialisiert und Stock-Blueprint registriert")
    return app


if __name__ == '__main__':
    app = create_app()
    # Standardport 5000, Host 0.0.0.0
    logger.info("Starte Flask-Server auf http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)