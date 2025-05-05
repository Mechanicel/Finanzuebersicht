import logging
import customtkinter as ctk
import requests
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from FrontendService.src.helpers.UniversalMethoden import clear_ui

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def create_screen(parent, title: str, api_endpoint: str, click_callback=None):
    """
    Erzeugt ein Tacho-Widget mit Titel und Wert von api_endpoint.
    Unterstützt JSON-Felder 'value', 'erfüllt' oder nested ETF-Einträge.
    Ein optionaler click_callback wird bei Klick auf das Chart ausgeführt.
    """
    logger.debug("GaugeScreen: Initialisiere '%s' mit Endpoint '%s'", title, api_endpoint)
    clear_ui(parent)

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=5, pady=5)

    ctk.CTkLabel(frame, text=title, font=("Arial", 14, "bold")).pack(pady=(0,5))

    # API-Aufruf
    try:
        base = os.getenv("BACKEND_URL", "http://127.0.0.1:5000")
        url = api_endpoint if api_endpoint.startswith("http") else f"{base}{api_endpoint}"
        logger.debug("GaugeScreen '%s': Abruf-URL=%s", title, url)

        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("GaugeScreen '%s': JSON-Antwort=%s", title, data)

        if "value" in data:
            val = float(data["value"])
        elif "erfüllt" in data:
            raw = data["erfüllt"]
            val = float(raw.strip().strip('%'))
        elif "etf" in data and isinstance(data["etf"], dict):
            first = next(iter(data["etf"].values()))
            val = float(first.get("erfüllt", "0%").strip().strip('%'))
        else:
            logger.error("GaugeScreen '%s': Keine erwarteten Felder", title)
            val = 0.0
    except Exception as e:
        logger.error("GaugeScreen '%s': Fehler beim Abruf – %s", title, e)
        val = 0.0

    # Zeichne Polar-Balken
    fig = Figure(figsize=(2,2), dpi=100)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(3.14)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.set_ylim(0,100)
    ax.barh(0, val, height=1.0, color="#3b8ed0")
    ax.text(0, 0, f"{val:.1f}%", ha='center', va='center', fontsize=16)

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Klick-Callback anbinden
    if click_callback:
        canvas.mpl_connect("button_press_event", lambda event: click_callback())

    return frame
