# src/screens/accountsummaryinnerScreens/TimeSeriesScreen.py

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkcalendar import DateEntry
from datetime import datetime, date
from FrontendService.src.helpers.UniversalMethoden import clear_ui
from FrontendService.src.models.AppState import AppState


def create_screen(app, navigator, state: AppState, **kwargs):
    clear_ui(app)

    # 1) Aktuelle Personendaten frisch laden
    person_data = state.selected_person
    if not person_data:
        return
    konten = person_data.get('Konten', [])

    # 2) Vorverarbeitung: Zeitreihen-Daten für jedes Konto
    dates_lists = []
    values_lists = []
    for konto in konten:
        ds, vs = [], []
        for ent in konto.get('Kontostaende', []):
            try:
                d_str, v_str = ent.split(': ')
                d = datetime.strptime(d_str, '%Y-%m-%d')
                v = float(v_str)
                ds.append(d)
                vs.append(v)
            except:
                continue
        dates_lists.append(ds)
        values_lists.append(vs)

    # 3) Layout: Chart links, Checkbox-Liste rechts, Date-Range unten
    chart_frame = ctk.CTkFrame(app)
    chart_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    filter_frame = ctk.CTkFrame(app)
    filter_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
    date_frame = ctk.CTkFrame(app)
    date_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    app.grid_columnconfigure(0, weight=3)
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(0, weight=1)

    # 4) Matplotlib-Figure und Canvas mit Toolbar
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    toolbar = NavigationToolbar2Tk(canvas, chart_frame)
    toolbar.update()
    toolbar.pack()

    # 5) Sichtbarkeits-Variablen und Checkboxen
    visible_vars = []
    ctk.CheckBoxLabel = ctk.CTkLabel  # Alias für Überschrift
    header = ctk.CTkLabel(filter_frame, text="Konten anzeigen:", font=("Arial", 14, "bold"))
    header.pack(anchor="nw", pady=(5, 10))
    for idx, konto in enumerate(konten):
        var = ctk.BooleanVar(value=True)
        visible_vars.append(var)
        name = f"{konto.get('Kontotyp','')} {konto.get('Kontonummer', konto.get('Deponummer',''))}"
        chk = ctk.CTkCheckBox(filter_frame, text=name, variable=var, command=lambda: update_plot())
        chk.pack(anchor="nw", pady=2)

    # 6) Date-Range-Widgets
    ctk.CTkLabel(date_frame, text="Von:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    from_entry = DateEntry(date_frame, date_pattern='yyyy-mm-dd')
    from_entry.set_date(date.today())
    from_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    ctk.CTkLabel(date_frame, text="Bis:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    to_entry = DateEntry(date_frame, date_pattern='yyyy-mm-dd')
    to_entry.set_date(date.today())
    to_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    ctk.CTkButton(
        date_frame, text="Aktualisieren",
        command=lambda: update_plot()
    ).grid(row=0, column=4, padx=10, pady=5)

    # 7) Plot-Update-Funktion
    def update_plot():
        ax.clear()
        d_from = from_entry.get_date()
        d_to   = to_entry.get_date()
        for i, var in enumerate(visible_vars):
            if var.get():
                ds = dates_lists[i]
                vs = values_lists[i]
                # Filter nach Datum
                ds_f, vs_f = [], []
                for d, v in zip(ds, vs):
                    if d_from <= d.date() <= d_to:
                        ds_f.append(d)
                        vs_f.append(v)
                ax.plot(ds_f, vs_f, label=konten[i].get('Kontotyp',''))
        ax.set_title('Zeitreihe der Kontostände')
        ax.set_xlabel('Datum')
        ax.set_ylabel('Saldo')
        ax.legend(loc='upper left', fontsize='small')
        ax.grid(True)
        canvas.draw()

    # 8) Initiales Rendern
    update_plot()
