# FrontendService/src/screens/analysis/TableScreen.py
import logging
import customtkinter as ctk
from tkinter import ttk
import requests
from FrontendService.src.helpers.UniversalMethoden import clear_ui

logger = logging.getLogger(__name__)


def create_screen(parent, api_endpoint: str):
    """
    Zeigt eine moderne Übersicht der 'basic' und 'metrics' Daten einer Aktie.
    Wenn beides vorhanden, in stylischen Sections; ansonsten generische Tabelle.
    """
    logger.debug("TableScreen: Initialisiere mit Endpoint %s", api_endpoint)
    clear_ui(parent)

    # Haupt-Scroll-Frame für Responsivität
    container = ctk.CTkScrollableFrame(parent)
    container.pack(fill="both", expand=True, padx=20, pady=20)
    container.grid_columnconfigure(0, weight=1)

    # API-Aufruf
    try:
        resp = requests.get(api_endpoint, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("TableScreen: Antwort JSON: %s", data)
    except Exception as e:
        logger.error("TableScreen: Fehler beim Abruf von %s – %s", api_endpoint, e)
        ctk.CTkLabel(container, text="Fehler beim Laden der Daten", text_color="red", font=(None, 14)).grid(pady=20)
        return

    # Moderne Darstellung basic & metrics
    if isinstance(data, dict) and "basic" in data and "metrics" in data:
        for section in ("basic", "metrics"):
            # Bereich als Frame mit Label-Überschrift
            box = ctk.CTkFrame(container, fg_color="#f0f0f0", corner_radius=10)
            box.grid(row=0 if section=='basic' else 1, column=0, sticky="ew", pady=(0,20))
            box.grid_columnconfigure(1, weight=1)
            # Überschrift
            ctk.CTkLabel(box, text=section.title(), font=(None, 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10,5))
            # Key-Value-Paare
            for i, (key, val) in enumerate(data[section].items(), start=1):
                ctk.CTkLabel(box, text=f"{key.title()}:", font=(None, 12, "bold")).grid(row=i, column=0, sticky="w", padx=(10,5), pady=4)
                ctk.CTkLabel(box, text=str(val), font=(None, 12)).grid(row=i, column=1, sticky="w", padx=(5,10), pady=4)
        logger.debug("TableScreen: basic und metrics in stylischen Sections angezeigt")
        return

    # Fallback: generische Baum-Tabelle mit Styling
    if not isinstance(data, list) or not data:
        ctk.CTkLabel(container, text="Keine Daten vorhanden", font=(None, 14)).grid(pady=20)
        return

    # Tabelle in eigenem Frame mit Scrollbar
    table_frame = ctk.CTkFrame(container)
    table_frame.grid(row=2, column=0, sticky="nsew")
    cols = list(data[0].keys())
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", style="Custom.Treeview")
    # Spalten-Header
    for c in cols:
        tree.heading(c, text=c.title())
        tree.column(c, anchor="w")
    tree.grid(row=0, column=0, sticky="nsew")
    # Scrollbar
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.grid(row=0, column=1, sticky="ns")
    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)
    # Daten einfügen mit alternierender Hintergrundfarbe
    for idx, rec in enumerate(data):
        tags = ("evenrow",) if idx % 2 == 0 else ("oddrow",)
        tree.insert("", "end", values=[rec.get(c, "") for c in cols], tags=tags)
    # Style definieren
    style = ttk.Style()
    style.configure("Custom.Treeview", rowheight=24, font=(None, 11))
    style.map("Custom.Treeview.Heading", font=[(None, 12, "bold")])
    style.configure("Custom.Treeview", background="#f7f7f7", fieldbackground="#f7f7f7")
    style.tag_configure("evenrow", background="#ffffff")
    style.tag_configure("oddrow", background="#ececec")

    logger.debug("TableScreen: generische Tabelle mit modernem Styling gefüllt")