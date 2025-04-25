# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/AktienAnalyseScreens/OptionChainScreen.py

import logging
import customtkinter as ctk

logger = logging.getLogger(__name__)

def create_option_chain_screen(parent, data: dict):
    """
    Zeigt Calls und Puts in zwei nebeneinander stehenden Tabellen.
    """
    logger.debug("Erstelle OptionChainScreen mit Daten: %s", data)
    frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    calls = data.get("calls", [])
    puts  = data.get("puts", [])
    exp   = data.get("expiration", "")

    ctk.CTkLabel(frame, text=f"Ablaufdatum: {exp}", font=("Arial",12,"bold"))\
       .pack(pady=(0,5))

    inner = ctk.CTkFrame(frame, fg_color="transparent")
    inner.pack(fill="both", expand=True)

    # Calls
    left = ctk.CTkFrame(inner, fg_color="transparent")
    left.pack(side="left", fill="both", expand=True, padx=5)
    ctk.CTkLabel(left, text="Calls", font=("Arial",12,"bold")).pack()
    _make_table(left, calls)

    # Puts
    right = ctk.CTkFrame(inner, fg_color="transparent")
    right.pack(side="left", fill="both", expand=True, padx=5)
    ctk.CTkLabel(right, text="Puts", font=("Arial",12,"bold")).pack()
    _make_table(right, puts)

def _make_table(parent, records):
    if not records:
        ctk.CTkLabel(parent, text="keine Daten").pack(pady=10)
        return
    keys = list(records[0].keys())
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x")
    for c, k in enumerate(keys):
        ctk.CTkLabel(header, text=k, anchor="w", width=100, font=("Arial",10,"bold"))\
           .grid(row=0, column=c, padx=2, pady=2)
    for rec in records:
        rowf = ctk.CTkFrame(parent, fg_color="transparent")
        rowf.pack(fill="x")
        for c, k in enumerate(keys):
            ctk.CTkLabel(rowf, text=str(rec.get(k, "")), anchor="w", width=100)\
               .grid(row=0, column=c, padx=2, pady=1)
