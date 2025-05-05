import os

# Basisverzeichnis für Caching
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Ordner für persistente Stock-Daten
DATA_DIR = os.getenv('STOCK_DATA_DIR', os.path.join(BASE_DIR, 'data', 'stocks'))

# Weitere Konfigurationswerte können hier ergänzt werden