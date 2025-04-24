# src/screens/accountsummaryinnerScreens/PieChartinnerScreens/DepoAnalyseScreens/AktienAnalyseScreen.py

import pprint
import customtkinter as ctk
from src.helpers.UniversalMethoden import clear_ui
from src.models import AppState

def create_screen(app, navigator, state: AppState, isin: str = None, **kwargs):
    clear_ui(app)
    if not isin:
        ctk.CTkLabel(app, text="Keine Aktie ausgewählt").pack(pady=20)
        return

    infos = state.stock_data_manager.get_stock_info(isin)

    # Container mit etwas Abstand
    container = ctk.CTkFrame(app, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=10)

    # Überschrift
    ctk.CTkLabel(
        container,
        text=f"Aktien-Kennzahlen für ISIN {isin}",
        font=("Arial", 16, "bold")
    ).pack(pady=(0,10))

    # Fehlermeldung (falls ausschließlich error vorhanden)
    err = infos.get("error")
    if err and len(infos) == 1:
        ctk.CTkLabel(container, text=f"Fehler: {err}", text_color="red").pack(pady=20)
        return
    # Warnung + weiter Tabs
    if err:
        ctk.CTkLabel(container, text=f"Warnung: {err}", text_color="orange").pack(pady=(0,10))

    # TabView anlegen
    tabs = ctk.CTkTabview(container, width=800, height=500)
    tabs.pack(fill="both", expand=True)

    # Für jede Sektion einen eigenen Tab
    for section, data in infos.items():
        if section == "error":
            continue
        tabs.add(section)

        tab_frame = tabs.tab(section)
        # scrollbarer Unter-Container
        scroll = ctk.CTkScrollableFrame(tab_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Einfache Werte & komplexe Strukturen trennen
        if isinstance(data, dict):
            for key, val in data.items():
                _render_item(scroll, key, val)
        elif isinstance(data, list):
            # Listen: jeden Eintrag nummeriert anzeigen
            for idx, item in enumerate(data, start=1):
                _render_item(scroll, f"{idx}", item)
        else:
            _render_item(scroll, section, data)

    # Helfer-Funktion zum Rendern eines einzelnen Items
def _render_item(parent, key, val):
    """
    Zeigt 'key: val' an.
    - Primitive Werte: Label
    - dict/list   : schickes, scrollbares Textfeld mit pprint-format
    """
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=2)

    # Key
    ctk.CTkLabel(row, text=f"{key}:", width=200, anchor="w").pack(side="left", padx=(0,10))

    # Value
    if isinstance(val, (dict, list)):
        # collapsible TextBox
        txt = ctk.CTkTextbox(parent, width=760, height=150, corner_radius=5)
        txt.insert("0.0", pprint.pformat(val, width=100))
        txt.configure(state="disabled")
        txt.pack(fill="both", padx=20, pady=(0,10))
    else:
        ctk.CTkLabel(row, text=str(val), anchor="w").pack(side="left")
