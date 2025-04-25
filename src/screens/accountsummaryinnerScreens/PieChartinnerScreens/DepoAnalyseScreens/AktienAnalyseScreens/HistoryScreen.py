import logging
import customtkinter as ctk
from datetime import timedelta, datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

from src.helpers.UniversalMethoden import clear_ui

logger = logging.getLogger(__name__)

def create_history_screen(parent, records: list):
    """
    Zeichnet einen kombinierten, interaktiven Chart der historischen Kurse:
      - Preise (Open, High, Low, Close) als Linien
      - Volumen als Balkendiagramm
      - Dividenden als grüne vertikale Linien
      - Aktiensplits als orangene gestrichelte Linien
      - Mouse-Hover-Tooltip für Linienpunkte und Dividend-Lines
      - Auswahl der Anzeigeperiode via Buttons (1d, 1w, 1m, 1y, 2y, 5y, 10y, all)
    """
    logger.debug("HistoryScreen: Eingangsdaten: %d Einträge", len(records))

    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    if not records:
        logger.debug("HistoryScreen: Keine Daten.")
        ctk.CTkLabel(frame, text="Keine historischen Kurse verfügbar").pack(pady=20)
        return

    title = ctk.CTkLabel(frame, text="Historische Kurse & Events", font=("Arial", 16, "bold"))
    title.pack(pady=(0,5))

    # Buttons für Periodenauswahl
    btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
    btn_frame.pack(fill="x", pady=(0,10), padx=20)
    def redraw(period):
        _redraw_chart(chart_container, records, period)

    periods = ["1d", "1w", "1m", "1y", "2y", "5y", "10y", "all"]
    for label in periods:
        btn = ctk.CTkButton(
            btn_frame,
            text=label,
            command=lambda l=label: redraw(l),
            width=50,
            height=30
        )
        btn.pack(side="left", padx=5)

    chart_container = ctk.CTkFrame(frame, fg_color="transparent")
    chart_container.pack(fill="both", expand=True)

    # Erster Plot: 1 Jahr
    redraw("1y")


def _redraw_chart(container, records, period):
    # Filter nach Zeitraum
    if period != "all":
        last_date = records[-1].get("Date")
        deltas = {
            "1d": timedelta(days=1),
            "1w": timedelta(weeks=1),
            "1m": timedelta(days=30),
            "1y": timedelta(days=365),
            "2y": timedelta(days=365*2),
            "5y": timedelta(days=365*5),
            "10y": timedelta(days=365*10)
        }
        delta = deltas.get(period)
        filtered = [r for r in records if r.get("Date") >= last_date - delta]
    else:
        filtered = records

    clear_ui(container)
    _plot_history(container, filtered)


def _plot_history(parent, records):
    dates = []
    price_data = {k: [] for k in ["Open", "High", "Low", "Close"]}
    volumes = []
    dividends = []
    splits = []

    for rec in records:
        dt = rec.get("Date")
        if not isinstance(dt, datetime):
            continue
        dates.append(dt)
        for key in price_data:
            price_data[key].append(rec.get(key, 0) or 0)
        volumes.append(rec.get("Volume", 0) or 0)
        div = rec.get("Dividends", 0) or 0
        if div:
            dividends.append((dt, div))
        if rec.get("Stock Splits", 0):
            splits.append(dt)

    x_nums = mdates.date2num(dates)

    fig = Figure(figsize=(6,6), dpi=100)
    ax1 = fig.add_subplot(2,1,1)
    ax2 = fig.add_subplot(2,1,2, sharex=ax1)

    lines = []
    for key, vals in price_data.items():
        ln, = ax1.plot_date(x_nums, vals, marker='o', linestyle='-', label=key, picker=5)
        lines.append(ln)

    div_lines = []
    for dt, val in dividends:
        x_val = mdates.date2num(dt)
        ln = ax1.axvline(x_val, color='green', linewidth=2, label='Dividend', picker=5)
        div_lines.append((ln, val))

    for dt in splits:
        x_val = mdates.date2num(dt)
        ax1.axvline(x_val, color='orange', linestyle='--', label='Stock Split')

    handles, labels = ax1.get_legend_handles_labels()
    unique = dict(zip(labels, handles))
    ax1.legend(
        unique.values(), unique.keys(),
        loc='upper left', bbox_to_anchor=(1.02, 1.0), borderaxespad=0,
        fontsize='small'
    )

    ax1.set_ylabel('Preis')
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2.bar(x_nums, volumes, width=0.8, alpha=0.5)
    ax2.set_ylabel('Volume')
    ax2.grid(True, linestyle='--', alpha=0.5)

    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate(rotation=45)

    annot = ax1.annotate(
        "", xy=(0,0), xytext=(15,15), textcoords='offset points',
        bbox=dict(boxstyle='round', fc='w'), arrowprops=dict(arrowstyle='->')
    )
    annot.set_visible(False)

    def update_annot(event, artist):
        x = event.xdata
        y = None
        label = ''
        if isinstance(artist, Line2D) and artist.get_label() != 'Dividend':
            xdata, ydata = artist.get_data()
            ind = artist.contains(event)[1]['ind'][0]
            x, y = xdata[ind], ydata[ind]
            label = artist.get_label()
        else:
            for ln, val in div_lines:
                if ln == artist:
                    y = ax1.get_ylim()[1]
                    label = f'Dividend: {val:.2f}'
                    break
        if x is None:
            return
        annot.xy = (x, y)
        date_str = mdates.num2date(x).strftime('%Y-%m-%d')
        annot.set_text(f"{label}\n{date_str}")
        annot.get_bbox_patch().set_alpha(0.8)

    def on_motion(event):
        if event.inaxes != ax1:
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return
        for artist in lines + [dl[0] for dl in div_lines]:
            cont, _ = artist.contains(event)
            if cont:
                update_annot(event, artist)
                annot.set_visible(True)
                fig.canvas.draw_idle()
                return
        if annot.get_visible():
            annot.set_visible(False)
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect('motion_notify_event', on_motion)

    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

    logger.debug("HistoryScreen: Darstellung fertig")
