import logging
from datetime import datetime
import customtkinter as ctk

logger = logging.getLogger(__name__)

def create_quarterly_income_screen(parent, records: list):
    """
    Zeigt quarterly_income_stmt als normale Tabelle:
      • Spalten: Feldnamen
      • Zeilen: Quartale (Datum)
    """
    logger.debug("Erstelle QuarterlyIncomeScreen mit %d Records", len(records))
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    if not records:
        ctk.CTkLabel(frame, text="Keine Daten vorhanden").pack(pady=20)
        return

    # 1) Spalten: Alle Felder außer 'index'
    fields = [k for k in records[0].keys() if k != "index"]
    fields = ["index"] + fields  # Datum an erste Stelle

    # 2) Header-Zeile
    for c, field in enumerate(fields):
        label = "Datum" if field == "index" else field
        ctk.CTkLabel(frame, text=label, anchor="w", font=("Arial", 12, "bold"))\
            .grid(row=0, column=c, sticky="w", padx=5, pady=4)

    # 3) Zeilenweise Daten
    for r, rec in enumerate(records, start=1):
        for c, field in enumerate(fields):
            val = rec.get(field, "")
            if field == "index":
                if hasattr(val, "strftime"):
                    val = val.strftime("%Y-%m-%d")
                else:
                    try:
                        val = datetime.fromisoformat(str(val)).strftime("%Y-%m-%d")
                    except Exception:
                        val = str(val)
            else:
                val = f"{val:,}" if isinstance(val, (int, float)) else str(val)

            ctk.CTkLabel(
                frame, text=val, anchor="e", font=("Arial", 11)
            ).grid(row=r, column=c, sticky="e", padx=5, pady=2)

    # 4) Gleichmäßige Spaltenbreite
    for col in range(len(fields)):
        frame.grid_columnconfigure(col, weight=1, uniform="quarterly")
