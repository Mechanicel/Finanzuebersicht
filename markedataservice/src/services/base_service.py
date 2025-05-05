import logging
from functools import wraps


def handle_errors(func):
    """
    Decorator für Service-Methoden, loggt Ausnahmen und leitet sie weiter.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Loggt die Exception mit Stack-Trace
            self.logger.exception(f"Fehler in {func.__name__}: {e}")
            raise
    return wrapper


class BaseService:
    """
    Basisklasse für alle Services, liefert einen Logger.
    """
    def __init__(self):
        # Logger pro Service-Klasse initialisieren
        self.logger = logging.getLogger(self.__class__.__name__)
