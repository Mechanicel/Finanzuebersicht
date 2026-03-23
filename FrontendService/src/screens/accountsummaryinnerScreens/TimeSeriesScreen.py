from datetime import datetime, date

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tkcalendar import DateEntry

from src.models.AppState import AppState
from src.ui.components import section_card, empty_state


def create_screen(app, navigator, state: AppState, **kwargs):
    person_data = state.selected_person
    if not person_data:
        empty_state(app, "Keine Person ausgewählt.")
        return

    konten = person_data.get("Konten", [])
    if not konten:
        empty_state(app, "Keine Konten vorhanden.")
        return

    dates_lists, values_lists = [], []
    for konto in konten:
        ds, vs = [], []
        for ent in konto.get("Kontostaende", []):
            try:
                d_str, v_str = ent.split(": ")
                ds.append(datetime.strptime(d_str, "%Y-%m-%d"))
                vs.append(float(v_str))
            except Exception:
                continue
        dates_lists.append(ds)
        values_lists.append(vs)

    if not any(values_lists):
        empty_state(app, "Keine Zeitreihendaten vorhanden.")
        return

    top_card, top_body = section_card(app, "Zeitreihenanalyse", "Filter links, Chart rechts")
    top_body.grid_columnconfigure(0, weight=1)
    top_body.grid_columnconfigure(1, weight=3)

    filter_frame = ctk.CTkFrame(top_body)
    filter_frame.grid(row=0, column=0, sticky="nswe", padx=(0, 8))
    chart_frame = ctk.CTkFrame(top_body)
    chart_frame.grid(row=0, column=1, sticky="nswe")

    ctk.CTkLabel(filter_frame, text="Konten anzeigen", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

    fig = Figure(figsize=(6.8, 4.3), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    toolbar = NavigationToolbar2Tk(canvas, chart_frame)
    toolbar.update()

    visible_vars = []
    for idx, konto in enumerate(konten):
        var = ctk.BooleanVar(value=True)
        visible_vars.append(var)
        name = f"{konto.get('Kontotyp', '')} {konto.get('Kontonummer', konto.get('Deponummer', ''))}".strip()
        ctk.CTkCheckBox(filter_frame, text=name, variable=var, command=lambda: update_plot()).pack(anchor="w", padx=10, pady=2)

    date_card, date_body = section_card(app, "Zeitraum")
    date_body.grid_columnconfigure((1, 3), weight=1)
    ctk.CTkLabel(date_body, text="Von").grid(row=0, column=0, sticky="w")
    from_entry = DateEntry(date_body, date_pattern="yyyy-mm-dd")
    from_entry.set_date(date.today())
    from_entry.grid(row=0, column=1, sticky="ew", padx=(8, 16))

    ctk.CTkLabel(date_body, text="Bis").grid(row=0, column=2, sticky="w")
    to_entry = DateEntry(date_body, date_pattern="yyyy-mm-dd")
    to_entry.set_date(date.today())
    to_entry.grid(row=0, column=3, sticky="ew", padx=(8, 16))
    ctk.CTkButton(date_body, text="Aktualisieren", command=lambda: update_plot()).grid(row=0, column=4, sticky="e")

    def update_plot():
        ax.clear()
        d_from = from_entry.get_date()
        d_to = to_entry.get_date()

        has_line = False
        for i, var in enumerate(visible_vars):
            if not var.get():
                continue
            ds_f, vs_f = [], []
            for d, v in zip(dates_lists[i], values_lists[i]):
                if d_from <= d.date() <= d_to:
                    ds_f.append(d)
                    vs_f.append(v)
            if ds_f:
                has_line = True
                ax.plot(ds_f, vs_f, label=konten[i].get("Kontotyp", "Konto"))

        ax.set_title("Zeitreihe der Kontostände")
        ax.set_xlabel("Datum")
        ax.set_ylabel("Saldo")
        ax.grid(True, alpha=0.3)
        if has_line:
            ax.legend(loc="upper left", fontsize="small")
        else:
            ax.text(0.5, 0.5, "Keine Daten im gewählten Zeitraum", ha="center", va="center", transform=ax.transAxes)
        canvas.draw()

    update_plot()
