# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/AktienAnalyseScreens/EarningsScreen.py

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

def create_earnings_screen(parent, records: list):
    """
    Zeigt earnings (Year, Earnings, Revenue) als Tabelle.
    """
    logger.debug("Erstelle EarningsScreen mit %d Einträgen", len(records) if records else 0)
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    if not records:
        ctk.CTkLabel(frame, text="Keine Daten").pack(pady=20)
        return

    keys = list(records[0].keys())
    header = ctk.CTkFrame(frame, fg_color="transparent")
    header.pack(fill="x")
    for c, k in enumerate(keys):
        ctk.CTkLabel(header, text=k, anchor="w", font=("Arial",12,"bold"))\
           .grid(row=0, column=c, padx=5, pady=2)

    for rec in records:
        rowf = ctk.CTkFrame(frame, fg_color="transparent")
        rowf.pack(fill="x")
        for c, k in enumerate(keys):
            ctk.CTkLabel(rowf, text=str(rec.get(k, "")), anchor="w")\
               .grid(row=0, column=c, padx=5, pady=1)
