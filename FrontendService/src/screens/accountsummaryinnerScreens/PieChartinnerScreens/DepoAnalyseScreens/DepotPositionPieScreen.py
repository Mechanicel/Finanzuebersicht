# src/screens/accountsummaryinnerScreens/DepotPositionPieScreen.py
import requests
import logging
from datetime import datetime
import customtkinter
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.helpers.UniversalMethoden import clear_ui
from src.models.AppState import AppState
from shared_config import get_settings

settings = get_settings()
BACKEND_URL = settings.marketdata_base_url.replace("0.0.0.0", "127.0.0.1").rstrip("/")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def create_screen(app, navigator, state: AppState,
                  depot_index,
                  pick_callback: callable = None,
                  **kwargs):
    logger.debug(f"create_screen: Öffne DepotPositionPieScreen für depot_index={depot_index}")
    clear_ui(app)
    logger.debug("DepoAnalyse: Ausgewählte Person: %s", state.selected_person)
    person = state.selected_person
    if not person:
        logger.warning("create_screen: Keine Person ausgewählt")
        return

    konten = person.get('Konten', [])
    if depot_index >= len(konten):
        logger.warning(f"create_screen: depot_index {depot_index} außerhalb der Konten-Liste")
        return

    konto = konten[depot_index]
    logger.debug(f"create_screen: Zeige Konto {konto.get('id')} vom Typ {konto.get('Kontotyp')}")

    labels, sizes = [], []
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    logger.debug(f"create_screen: Verwende Datum {date_str} für Preisabfrage")
    logger.debug(f"create_screen: API-Basis-URL: {BACKEND_URL}")

    for det in konto.get('DepotDetails', []):
        isin = det.get('ISIN', '').strip()
        try:
            menge = float(det.get('Menge', 0) or 0)
        except Exception as e:
            logger.error(f"create_screen: Ungültige Menge {det} – {e}")
            menge = 0.0

        # Preis abrufen
        price_url = f"{BACKEND_URL}/price/{isin}"
        try:
            resp_price = requests.get(price_url, params={"date": date_str}, timeout=5)
            resp_price.raise_for_status()
            price = resp_price.json().get("price", 0.0)
            logger.debug(f"create_screen: GET {resp_price.url} → {price}")
        except Exception as e:
            logger.error(f"create_screen: Fehler Preis für {isin} ({price_url}) – {e}")
            price = 0.0

        # Firmenname abrufen
        comp_url = f"{BACKEND_URL}/company/{isin}"
        try:
            resp_comp = requests.get(comp_url, timeout=5)
            resp_comp.raise_for_status()
            company = resp_comp.json().get("company_name") or isin
            logger.debug(f"create_screen: GET {resp_comp.url} → {company}")
        except Exception as e:
            logger.error(f"create_screen: Fehler Company für {isin} ({comp_url}) – {e}")
            company = isin

        value = price * menge
        logger.debug(f"create_screen: ISIN={isin}, Menge={menge}, Preis={price}, Wert={value}")
        labels.append(company)
        sizes.append(value)

    # Zeichne Pie
    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_title("Depot-Aufteilung")

    if not any(sizes):
        logger.info("create_screen: Keine Depot-Positionen – Platzhalter")
        ax.text(0.5, 0.5, 'Keine Positionen', ha='center', va='center')
    else:
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        for w in wedges:
            w.set_picker(True)
        logger.debug(f"create_screen: {len(wedges)} Wedges erstellt")

        def on_pick(event):
            w = event.artist
            try:
                idx = wedges.index(w)
            except ValueError:
                logger.error("on_pick: Gewedge nicht gefunden")
                return
            sel_isin = konto["DepotDetails"][idx].get("ISIN")
            logger.debug(f"on_pick: Gewedge {idx} angeklickt, ISIN={sel_isin}")
            if pick_callback:
                pick_callback({"event": "stock_selected", "isin": sel_isin})

        canvas = FigureCanvasTkAgg(fig, master=app)
        canvas.mpl_connect("pick_event", on_pick)

    canvas = FigureCanvasTkAgg(fig, master=app)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
    logger.debug("create_screen: Fertig")
