# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/AktienAnalyseScreens/PriceTargetsScreen.py

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

def create_price_targets_screen(parent, data: dict):
    """
    Zeigt Analysten-Price-Targets in einer Tabelle:
      Datum │ Low │ Mean │ High
    """
    logger.debug("Erstelle PriceTargetsScreen mit Daten: %s", data)
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # alle Zeitpunkte sammeln
    idxs = set()
    for col_dict in data.values():
        idxs.update(col_dict.keys())
    idxs = sorted(idxs)
    cols = list(data.keys())

    # Header
    for c, col in enumerate(["Datum"] + cols):
        ctk.CTkLabel(frame, text=col, anchor="w", font=("Arial",12,"bold"))\
           .grid(row=0, column=c, sticky="w", padx=5, pady=2)

    # Rows
    for r, idx in enumerate(idxs, start=1):
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
        ctk.CTkLabel(frame, text=date_str, anchor="w")\
           .grid(row=r, column=0, sticky="w", padx=5, pady=1)
        for c, col in enumerate(cols, start=1):
            val = data.get(col, {}).get(idx, "")
            ctk.CTkLabel(frame, text=str(val), anchor="w")\
               .grid(row=r, column=c, sticky="w", padx=5, pady=1)
