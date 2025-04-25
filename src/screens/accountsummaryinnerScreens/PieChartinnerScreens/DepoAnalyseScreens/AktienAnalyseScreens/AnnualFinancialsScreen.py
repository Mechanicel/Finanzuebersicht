import logging
import customtkinter as ctk
from datetime import datetime

logger = logging.getLogger(__name__)


def create_annual_financials_screen(parent, data: dict):
    """
    Zeigt annual_financials als Pivot-Tabelle:
      Posten ↓ │ Jahr_n │ Jahr_n-1 │ … (absteigend nach Jahr)
    """
    logger.debug("Erstelle AnnualFinancialsScreen mit %d Posten (rohe Daten)", len(data))

    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    if not data:
        logger.debug("AnnualFinancialsScreen: Keine Daten vorhanden")
        ctk.CTkLabel(frame, text="Keine Daten").pack(pady=20)
        return

    # Bei yfinance: data orientiert als {Timestamp: {Feld: Wert}}, daher transponieren
    first_key = next(iter(data.keys()))
    if isinstance(first_key, datetime):
        logger.debug("AnnualFinancialsScreen: Spaltenorientierte Daten erkannt, transpose")
        transposed = {}
        for year, inner in data.items():
            for field, val in inner.items():
                transposed.setdefault(field, {})[year] = val
        data = transposed
        logger.debug("AnnualFinancialsScreen: Nach Transpose %d Felder", len(data))

    # Sortiere Felder alphabetisch für Konsistenz
    fields = sorted(data.keys(), key=lambda s: s.lower())
    # Sammle alle Jahre und sortiere absteigend (neuestes Jahr zuerst)
    years = sorted(
        {yr for fld in fields for yr in data[fld].keys()},
        key=lambda x: str(x),
        reverse=True
    )
    logger.debug("AnnualFinancialsScreen: Felder = %s", fields)
    logger.debug("AnnualFinancialsScreen: Jahre = %s", years)

    # --- Header ---
    ctk.CTkLabel(frame, text="", width=150).grid(row=0, column=0, padx=5, pady=5)
    for col, yr in enumerate(years, start=1):
        label = yr.strftime("%Y") if hasattr(yr, "strftime") else str(yr)
        ctk.CTkLabel(
            frame,
            text=label,
            anchor="w",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=col, padx=5, pady=5, sticky="w")

    # --- Datenzeilen ---
    for r, fld in enumerate(fields, start=1):
        ctk.CTkLabel(
            frame,
            text=fld,
            width=150,
            anchor="w",
            font=("Arial", 11, "bold")
        ).grid(row=r, column=0, padx=5, pady=2, sticky="w")

        for c, yr in enumerate(years, start=1):
            val = data.get(fld, {}).get(yr, None)
            if isinstance(val, (int, float)):
                text = f"{val:,.0f}"
            else:
                text = "" if val is None else str(val)
            ctk.CTkLabel(
                frame,
                text=text,
                anchor="e",
                font=("Arial", 11)
            ).grid(row=r, column=c, padx=5, pady=2, sticky="e")

    # --- Spalten-Gewichte für gleichmäßiges Layout ---
    total_cols = len(years) + 1
    for col in range(total_cols):
        frame.grid_columnconfigure(col, weight=1, uniform="annual")

    logger.debug("AnnualFinancialsScreen: Darstellung fertig")