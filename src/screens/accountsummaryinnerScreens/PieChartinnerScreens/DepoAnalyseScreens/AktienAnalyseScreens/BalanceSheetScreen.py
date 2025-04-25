# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/AktienAnalyseScreens/BalanceSheetScreen.py

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

def create_balance_sheet_screen(parent, data: dict):
    """
    Zeigt die drei zentralen Bilanzposten über die Jahre:
      • Gesamtvermögen
      • Verbindlichkeiten gesamt
      • Eigenkapital gesamt
    """
    logger.debug("Erstelle BalanceSheetScreen mit Daten: %s", data)
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    fields = [
        ("Gesamtvermögen",            "Total Assets"),
        ("Verbindlichkeiten gesamt",  "Total Liab"),
        ("Eigenkapital gesamt",       "Total Stockholder Equity")
    ]
    years = sorted({yr for _, fld in fields for yr in data.get(fld, {}).keys()}, key=lambda x: str(x), reverse=True)

    if not years:
        ctk.CTkLabel(frame, text="Keine Bilanz-Daten verfügbar").pack(pady=20)
        return

    # Header
    header = ctk.CTkFrame(frame, fg_color="transparent")
    header.pack(fill="x", pady=(0,5))
    ctk.CTkLabel(header, text="", width=200).grid(row=0, column=0, padx=5)
    for c, yr in enumerate(years, start=1):
        ctk.CTkLabel(header, text=str(yr), anchor="w", font=("Arial",12,"bold"))\
           .grid(row=0, column=c, sticky="w", padx=5)

    # Rows
    for r, (label, fld) in enumerate(fields, start=1):
        rowf = ctk.CTkFrame(frame, fg_color="transparent")
        rowf.pack(fill="x", pady=2)
        ctk.CTkLabel(rowf, text=label, width=200, anchor="w")\
           .grid(row=0, column=0, sticky="w", padx=5)
        for c, yr in enumerate(years, start=1):
            val = data.get(fld, {}).get(yr, "")
            text = f"{val:,.0f}" if isinstance(val, (int,float)) else str(val)
            ctk.CTkLabel(rowf, text=text, anchor="e", width=120)\
               .grid(row=0, column=c, sticky="e", padx=5)
