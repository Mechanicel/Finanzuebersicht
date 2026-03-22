import os
import json
import logging
from typing import Any, Dict, Optional

from src.utils.config import DATA_DIR

logger = logging.getLogger(__name__)

class FileRepository:
    """
    Repository für das Caching von StockModel-Daten in JSON-Dateien.
    Jede ISIN bekommt eine eigene Datei im DATA_DIR.
    """
    def __init__(self, data_dir: Optional[str] = None):
        # Erlaube Überschreibung des Datenverzeichnisses
        self.data_dir = data_dir or DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        logger.debug(f"[FileRepository] Using data directory: {self.data_dir}")

    def _file_path(self, isin: str) -> str:
        # Dateiname nach ISIN.json
        return os.path.join(self.data_dir, f"{isin}.json")

    def read(self, isin: str) -> Optional[Dict[str, Any]]:
        """
        Liest die Datei für die gegebene ISIN und gibt das JSON-Objekt zurück.
        Falls die Datei nicht existiert oder ungültiges JSON enthält, wird None zurückgegeben.
        """
        path = self._file_path(isin)
        logger.debug(f"[FileRepository] Lese Datei: {path}")
        if not os.path.isfile(path):
            logger.debug(f"[FileRepository] Datei nicht gefunden für ISIN={isin}")
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"[FileRepository] Geladene Daten: {list(data.keys())}")
            return data
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"[FileRepository] Fehler beim Lesen der Datei {path}: {e}")
            return None

    def write(self, isin: str, data: Dict[str, Any]) -> None:
        """
        Schreibt das gegebene Dict als JSON in die Datei für die ISIN.
        Bestehende Dateien werden überschrieben.
        """
        path = self._file_path(isin)
        logger.debug(f"[FileRepository] Schreibe Datei: {path}")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"[FileRepository] Erfolgreich geschrieben für ISIN={isin}")
        except IOError as e:
            logger.error(f"[FileRepository] Fehler beim Schreiben der Datei {path}: {e}")
            raise
