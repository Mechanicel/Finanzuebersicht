# FrontendService/src/screens/analysis/ChartScreen.py
import logging
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
from datetime import datetime
import requests
from urllib.parse import urlparse, parse_qs
from src.helpers.UniversalMethoden import clear_ui
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ColumnSelectorScreen import create_column_selector_screen

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def create_screen(parent, api_endpoint: str):
    """
    Zeigt ein Liniendiagramm der historischen Daten.
    Nutzt JSON mit 'entries' oder verschachtelte 'etf' Sektionen.
    ColumnSelector erlaubt Ein-/Ausblenden einzelner Kennzahlen.
    Das Feld 'country' wird nur oben als Label angezeigt.
    Die Y-Achse wird manuell anhand aktiver Serien neu skaliert und in Millionen formatiert.
    Die X-Achse zeigt ausgewählte Datumswerte aufsteigend.
    """
    logger.debug("ChartScreen: Initialisiere mit Endpoint %s", api_endpoint)
    clear_ui(parent)

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Titel
    ctk.CTkLabel(frame, text="Historische Entwicklung", font=(None, 16, "bold")).pack(pady=(0,5))

    # API-Abfrage
    try:
        resp = requests.get(api_endpoint, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.debug("ChartScreen: Rohdaten: %s", data)
    except Exception as e:
        logger.error("ChartScreen: Fehler beim Abruf von %s – %s", api_endpoint, e)
        ctk.CTkLabel(frame, text="Fehler beim Laden der Daten", text_color="red").pack(pady=20)
        return

    # historische Einträge extrahieren
    entries = data.get("entries")
    if not entries:
        parsed = urlparse(api_endpoint)
        etf = parse_qs(parsed.query).get("etf", [None])[0]
        entries = data.get("etf", {}).get(etf, {}).get("entries", [])
    if not entries:
        ctk.CTkLabel(frame, text="Keine historischen Daten gefunden").pack(pady=20)
        return

    # Land-Label
    country = entries[0].get("country")
    if country:
        ctk.CTkLabel(frame, text=f"Land: {country}", font=(None, 12)).pack(pady=(0,10))

    # numerische Kennzahlen erkennen
    metrics = []
    for key in entries[0].keys():
        if key in ("date", "country"): continue
        try:
            for e in entries:
                float(e.get(key, 0))
            metrics.append(key)
        except:
            continue
    logger.debug("ChartScreen: Zu plottende Kennzahlen: %s", metrics)

    # Container für Chart & Selector
    chart_container = ctk.CTkFrame(frame, fg_color="transparent")
    chart_container.pack(fill="both", expand=True)
    selector_container = ctk.CTkFrame(frame, fg_color="transparent")
    selector_container.pack(fill="x", pady=(5,0))

    # Matplotlib-Figur
    fig = Figure(figsize=(5,3), dpi=100)
    ax = fig.add_subplot(111)

    # Daten speichern und Linien anlegen
    lines = {}
    data_map = {}
    # Datumsstrings in datetime-Objekte und sortieren aufsteigend
    entries_sorted = sorted(entries, key=lambda e: datetime.strptime(e['date'], '%Y-%m-%d'))
    dates = [datetime.strptime(e['date'], '%Y-%m-%d') for e in entries_sorted]

    for name in metrics:
        ys = [float(e.get(name, 0)) for e in entries_sorted]
        ln, = ax.plot(dates, ys, label=name)
        lines[name] = ln
        data_map[name] = ys

    # initiale Skalierung und Formatierung
    def rescale():
        # alle sichtbaren Serien
        visible_vals = [val for nm, ys in data_map.items() if lines[nm].get_visible() for val in ys]
        if visible_vals:
            mn, mx = min(visible_vals), max(visible_vals)
            padding = (mx - mn) * 0.1
            ax.set_ylim(mn - padding, mx + padding)
        # Datumsformatierung
        ax.set_xlim(min(dates), max(dates))
        ax.relim()
        # Millionen-Formatierung
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x/1e6:.1f}M"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))

    rescale()
    ax.set_xlabel("Datum")
    ax.set_ylabel("Wert in Mio.")
    ax.legend()

    canvas = FigureCanvasTkAgg(fig, master=chart_container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    # Toggle via ColumnSelector
    def toggle(col):
        ln = lines[col]
        ln.set_visible(not ln.get_visible())
        rescale()
        canvas.draw()
        logger.debug("ChartScreen: Serie '%s' sichtbar=%s", col, ln.get_visible())

    create_column_selector_screen(
        selector_container,
        metrics,
        lambda c, _: toggle(c)
    )
    logger.debug("ChartScreen: Fertig aufgebaut")