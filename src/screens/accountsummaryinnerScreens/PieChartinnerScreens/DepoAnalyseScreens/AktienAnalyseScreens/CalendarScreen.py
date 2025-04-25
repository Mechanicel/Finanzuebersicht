import logging
import customtkinter as ctk
from datetime import datetime

logger = logging.getLogger(__name__)

def create_calendar_screen(parent, data: dict):
    """
    Zeigt das Earnings-Kalender-Dict als tabellarische Liste:
      Datum      │ Ereignis
      (chronologisch sortiert)
    """
    logger.debug("Erstelle CalendarScreen mit %d Einträgen", len(data))

    # Scrollbarer Container
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    if not data:
        logger.debug("CalendarScreen: Keine Daten vorhanden")
        ctk.CTkLabel(frame, text="Keine Kalenderdaten verfügbar").pack(pady=20)
        return

    # Sortiere nach Datum
    try:
        items = sorted(
            data.items(),
            key=lambda kv: kv[0] if isinstance(kv[0], datetime) else datetime.fromisoformat(str(kv[0]))
        )
    except Exception:
        logger.exception("CalendarScreen: Fehler beim Sortieren der Termine")
        items = list(data.items())

    # Header
    ctk.CTkLabel(
        frame, text="Datum", anchor="w", width=150,
        font=("Arial", 12, "bold")
    ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
    ctk.CTkLabel(
        frame, text="Ereignis", anchor="w",
        font=("Arial", 12, "bold")
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)

    # Datenzeilen
    for r, (key, val) in enumerate(items, start=1):
        # Datum formatieren
        if isinstance(key, datetime):
            date_str = key.strftime("%Y-%m-%d %H:%M") if key.time() != datetime.min.time() else key.strftime("%Y-%m-%d")
        else:
            try:
                dt = datetime.fromisoformat(str(key))
                date_str = dt.strftime("%Y-%m-%d %H:%M") if dt.time() != datetime.min.time() else dt.strftime("%Y-%m-%d")
            except Exception:
                date_str = str(key)

        ctk.CTkLabel(
            frame, text=date_str, anchor="w", width=150
        ).grid(row=r, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(
            frame, text=str(val), anchor="w"
        ).grid(row=r, column=1, sticky="w", padx=5, pady=2)

    # Layout: zwei Spalten gleichmäßig
    frame.grid_columnconfigure(0, weight=1, uniform="cal")
    frame.grid_columnconfigure(1, weight=3, uniform="cal")

    logger.debug("CalendarScreen: Darstellung fertig")