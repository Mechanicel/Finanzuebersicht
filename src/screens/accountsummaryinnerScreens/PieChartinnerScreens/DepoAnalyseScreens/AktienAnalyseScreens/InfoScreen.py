# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/AktienAnalyseScreens/InfoScreen.py

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

def create_info_screen(parent, data: dict):
    """
    Zeigt Basis-Kennzahlen aus ticker.info als Key-Value-Liste.
    """
    logger.debug("Erstelle InfoScreen mit Daten: %s", data)
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    row = 0
    for key, val in data.items():
        ctk.CTkLabel(frame, text=f"{key}:", anchor="w", width=200)\
           .grid(row=row, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(frame, text=str(val), anchor="w")\
           .grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1
