import logging
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from finanzuebersicht_shared import get_settings
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient
from src.ui.components import create_page, empty_state, section_card

logger = logging.getLogger(__name__)
settings = get_settings()

BENCHMARKS = {
    "msci_world": "MSCI World",
    "sp500": "S&P 500",
    "ftse_all_world": "FTSE All-World",
}


def _to_float(value):
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt_number(value, digits: int = 2):
    val = _to_float(value)
    return "—" if val is None else f"{val:,.{digits}f}".replace(",", " ")


def _fmt_currency(value, currency: str = "EUR", digits: int = 2):
    val = _to_float(value)
    return "—" if val is None else f"{val:,.{digits}f} {currency}".replace(",", " ")


def _fmt_percent(value, digits: int = 2):
    val = _to_float(value)
    return "—" if val is None else f"{val * 100:.{digits}f}%"


def _display_value(value):
    if value in (None, ""):
        return "—"
    return str(value)


def _kpi_grid(parent, items: list[tuple[str, str]], columns: int = 4):
    grid = ctk.CTkFrame(parent, fg_color="transparent")
    grid.pack(fill="x", pady=(6, 12))
    for col in range(columns):
        grid.grid_columnconfigure(col, weight=1)

    for idx, (label, value) in enumerate(items):
        row = idx // columns
        col = idx % columns
        card = ctk.CTkFrame(grid, corner_radius=10)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="ew")
        ctk.CTkLabel(card, text=label, text_color="gray70", font=("Arial", 11)).pack(anchor="w", padx=10, pady=(8, 0))
        ctk.CTkLabel(card, text=value, font=("Arial", 17, "bold")).pack(anchor="w", padx=10, pady=(2, 8))


def _build_line_chart(parent, title: str, series_map: dict[str, list[tuple[datetime, float]]], percent_axis: bool = False):
    card, body = section_card(parent, title)
    usable = {name: points for name, points in series_map.items() if points}
    if not usable:
        empty_state(body, "Keine Zeitreihen-Daten vorhanden")
        return card

    body.grid_columnconfigure(0, weight=1)
    body.grid_rowconfigure(0, weight=1)

    fig = Figure(figsize=(6, 3), dpi=100)
    ax = fig.add_subplot(111)
    lines = {}

    for name, points in usable.items():
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        ln, = ax.plot(xs, ys, label=name)
        lines[name] = ln

    ax.grid(alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    if percent_axis:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x * 100:.1f}%"))

    canvas = FigureCanvasTkAgg(fig, master=body)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", pady=(0, 6))

    toggle_row = ctk.CTkFrame(body, fg_color="transparent")
    toggle_row.grid(row=1, column=0, sticky="ew")
    for i, name in enumerate(lines.keys()):
        var = ctk.BooleanVar(value=True)

        def _toggle(n=name, v=var):
            lines[n].set_visible(v.get())
            ax.relim()
            ax.autoscale_view()
            canvas.draw_idle()

        cb = ctk.CTkCheckBox(toggle_row, text=name, variable=var, command=_toggle)
        cb.grid(row=0, column=i, padx=8, pady=2, sticky="w")

    return card


def _render_simple_table(parent, title: str, rows: list[dict], max_rows: int = 12):
    card, body = section_card(parent, title)
    if not rows:
        empty_state(body, "Keine Daten vorhanden")
        return

    table_frame = ctk.CTkFrame(body)
    table_frame.pack(fill="x", expand=False)

    cols = list(rows[0].keys())
    tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=min(max_rows, len(rows)))
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=130, anchor="w")

    for row in rows[:max_rows]:
        tree.insert("", "end", values=[_display_value(row.get(col)) for col in cols])

    yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=yscroll.set)
    tree.grid(row=0, column=0, sticky="nsew")
    yscroll.grid(row=0, column=1, sticky="ns")
    table_frame.grid_columnconfigure(0, weight=1)


def _extract_series(points: list[dict], key: str):
    out = []
    for point in points:
        if not isinstance(point, dict):
            continue
        raw_date = point.get("date")
        value = _to_float(point.get(key))
        if not raw_date or value is None:
            continue
        try:
            out.append((datetime.fromisoformat(raw_date), value))
        except ValueError:
            continue
    return out


def _build_position_info(state, depot_index: int, selected_isin: str, current_price: float | None):
    person = state.selected_person or {}
    konten = person.get("Konten", []) if isinstance(person, dict) else []
    if depot_index >= len(konten):
        return {"position_value": None, "weight": None, "performance": None, "quantity": None}

    account = konten[depot_index]
    details = account.get("DepotDetails", []) if isinstance(account, dict) else []
    selected = None
    total = 0.0

    for row in details:
        isin = str(row.get("ISIN", "")).strip().upper()
        qty = _to_float(row.get("Menge")) or 0.0
        if isin == selected_isin.upper():
            selected = row
        try:
            px = state.data_manager.get_price(isin, datetime.utcnow().date())
        except Exception:
            px = 0.0
        total += qty * (px or 0.0)

    if not selected:
        return {"position_value": None, "weight": None, "performance": None, "quantity": None}

    qty = _to_float(selected.get("Menge"))
    position_value = None if qty is None or current_price is None else qty * current_price

    buy_price = _to_float(
        selected.get("Einstandspreis")
        or selected.get("Kaufpreis")
        or selected.get("Anschaffungspreis")
        or selected.get("Durchschnittspreis")
    )
    performance = None
    if buy_price not in (None, 0.0) and current_price is not None:
        performance = (current_price / buy_price) - 1.0

    weight = None
    if position_value is not None and total > 0:
        weight = position_value / total

    return {"position_value": position_value, "weight": weight, "performance": performance, "quantity": qty}


def create_screen(app, navigator, state, depot_index: int = 0, **kwargs):
    ui = create_page(
        app,
        "Depot-Analyse",
        "Analyse-Workspace für Unternehmens- und Wertpapierdaten",
        back_command=lambda: navigator.navigate("AccountSummary", selected_tab="piechart"),
        scrollable=True,
    )
    client = AnalysisApiClient(settings.marketdata_base_url)

    _, top_body = section_card(ui["content"], "Depot-Aufteilung", "Klicken Sie auf eine Position, um den Workspace zu laden.")
    _, workspace_body = section_card(ui["content"], "Analyse-Workspace")

    placeholder = empty_state(workspace_body, "Bitte oben eine Position auswählen.")

    def _render_workspace(isin: str):
        nonlocal placeholder
        for widget in workspace_body.winfo_children():
            widget.destroy()

        full, full_error = client.load_full(isin)
        metrics, metrics_error = client.load_metrics(isin)
        analysts, _ = client.load_analysts(isin)
        fund, _ = client.load_fund(isin)

        if full_error:
            empty_state(workspace_body, f"Analyse konnte nicht geladen werden: {full_error}")
            return
        if not full:
            empty_state(workspace_body, "Keine Analyse-Daten verfügbar")
            return

        instrument = full.get("instrument", {}) if isinstance(full.get("instrument"), dict) else {}
        market = full.get("market", {}) if isinstance(full.get("market"), dict) else {}
        profile = full.get("profile", {}) if isinstance(full.get("profile"), dict) else {}
        timeseries = full.get("timeseries", {}) if isinstance(full.get("timeseries"), dict) else {}
        metrics_payload = metrics.get("metrics", {}) if isinstance(metrics, dict) else {}
        analysts_payload = analysts.get("analysts", {}) if isinstance(analysts, dict) else full.get("analysts", {})
        fund_payload = fund.get("fund", {}) if isinstance(fund, dict) else full.get("fund", {})

        currency = market.get("currency") or instrument.get("currency") or "EUR"
        current_price = _to_float(market.get("currentPrice"))
        prev_close = _to_float(market.get("previousClose"))
        day_change = None
        if current_price is not None and prev_close not in (None, 0.0):
            day_change = (current_price / prev_close) - 1.0

        pos = _build_position_info(state, depot_index, isin, current_price)

        header, header_body = section_card(workspace_body, "Instrument")
        header_body.grid_columnconfigure((0, 1, 2), weight=1)

        name = instrument.get("long_name") or instrument.get("short_name") or instrument.get("symbol") or isin
        ctk.CTkLabel(header_body, text=name, font=("Arial", 23, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
        ctk.CTkLabel(
            header_body,
            text=(
                f"Symbol: {_display_value(instrument.get('symbol'))}   |   "
                f"ISIN: {_display_value(instrument.get('isin') or isin)}"
            ),
            text_color="gray70",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 8))

        _kpi_grid(
            header_body,
            [
                ("Aktueller Kurs", _fmt_currency(current_price, currency)),
                ("Tagesveränderung", _fmt_percent(day_change)),
                ("Sektor / Branche", f"{_display_value(profile.get('sector'))} / {_display_value(profile.get('industry'))}"),
                ("Land / Börse", f"{_display_value(profile.get('country'))} / {_display_value(instrument.get('exchange'))}"),
                ("Positionswert", _fmt_currency(pos.get("position_value"), currency)),
                ("Gewichtung im Depot", _fmt_percent(pos.get("weight"))),
                ("Positions-Performance", _fmt_percent(pos.get("performance"))),
                ("Menge", _fmt_number(pos.get("quantity"), 4)),
            ],
            columns=4,
        )

        if metrics_error:
            ctk.CTkLabel(header_body, text=f"Hinweis: {metrics_error}", text_color="#ffb347").grid(row=3, column=0, sticky="w")

        tabview = ctk.CTkTabview(workspace_body)
        tabview.pack(fill="both", expand=True, pady=(8, 0))

        overview_tab = tabview.add("Überblick")
        fundamentals_tab = tabview.add("Fundamentals")
        valuation_tab = tabview.add("Bewertung")
        risk_tab = tabview.add("Risiko & Performance")
        analysts_tab = tabview.add("Analysten")

        show_etf = str((instrument.get("quote_type") or fund_payload.get("quoteType") or "")).upper() in {"ETF", "MUTUALFUND"}
        etf_tab = tabview.add("ETF-Exposure") if show_etf else None

        # Überblick
        performance = metrics_payload.get("performance", {}) if isinstance(metrics_payload, dict) else {}
        growth = metrics_payload.get("growth", {}) if isinstance(metrics_payload, dict) else {}
        profitability = metrics_payload.get("profitability", {}) if isinstance(metrics_payload, dict) else {}

        _kpi_grid(
            overview_tab,
            [
                ("Marktkapitalisierung", _fmt_currency(market.get("marketCap"), currency, 0)),
                ("52W Hoch", _fmt_currency(market.get("fiftyTwoWeekHigh"), currency)),
                ("52W Tief", _fmt_currency(market.get("fiftyTwoWeekLow"), currency)),
                ("Volatilität", _fmt_percent((performance.get("volatility") or {}).get("value"))),
                ("Sharpe", _fmt_number((performance.get("sharpe_ratio") or {}).get("value"), 2)),
                ("Max Drawdown", _fmt_percent((performance.get("max_drawdown") or {}).get("value"))),
                ("Revenue-Wachstum", _fmt_percent((growth.get("revenue_growth") or {}).get("value"))),
                ("Net Margin", _fmt_percent((profitability.get("net_margin") or {}).get("value"))),
            ],
            columns=4,
        )

        profile_card, profile_body = section_card(overview_tab, "Kurzprofil")
        ctk.CTkLabel(
            profile_body,
            text=_display_value(profile.get("business_summary")),
            justify="left",
            wraplength=1000,
            text_color="gray80",
        ).pack(anchor="w")

        price_history = timeseries.get("price_history", []) if isinstance(timeseries, dict) else []
        _build_line_chart(overview_tab, "Preis-Chart", {"Close": _extract_series(price_history, "close")}, percent_axis=False)

        # Fundamentals
        period_row = ctk.CTkFrame(fundamentals_tab, fg_color="transparent")
        period_row.pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(period_row, text="Zeitraum:").pack(side="left", padx=(0, 8))
        period_var = ctk.StringVar(value="annual")

        tables_container = ctk.CTkFrame(fundamentals_tab, fg_color="transparent")
        tables_container.pack(fill="both", expand=True)

        def render_financials(period: str):
            for w in tables_container.winfo_children():
                w.destroy()
            payload, err = client.load_financials(isin, period)
            if err or not payload:
                empty_state(tables_container, err or "Keine Financials verfügbar")
                return

            financials = payload.get("financials", {})
            income = (financials.get("income_statement", {}) or {}).get(period, [])
            balance = (financials.get("balance_sheet", {}) or {}).get(period, [])
            cash_flow = (financials.get("cash_flow", {}) or {}).get(period, [])

            _render_simple_table(tables_container, "Income Statement", income)
            _render_simple_table(tables_container, "Balance Sheet", balance)
            _render_simple_table(tables_container, "Cash Flow", cash_flow)

            _build_line_chart(
                tables_container,
                "Revenue / EPS / FCF / Margen",
                {
                    "Revenue": _extract_series(income, "Total Revenue") or _extract_series(income, "Revenue"),
                    "EPS": _extract_series(income, "Diluted EPS") or _extract_series(income, "Basic EPS"),
                    "Free Cash Flow": _extract_series(cash_flow, "Free Cash Flow"),
                    "Operating Margin": _extract_series(income, "Operating Margin"),
                },
            )

        segmented = ctk.CTkSegmentedButton(period_row, values=["annual", "quarterly"], variable=period_var, command=render_financials)
        segmented.pack(side="left")
        render_financials(period_var.get())

        # Bewertung
        valuation = full.get("valuation", {}) if isinstance(full.get("valuation"), dict) else {}
        _kpi_grid(
            valuation_tab,
            [
                ("Trailing PE", _fmt_number(valuation.get("trailingPE"), 2)),
                ("Forward PE", _fmt_number(valuation.get("forwardPE"), 2)),
                ("EV/Sales", _fmt_number(valuation.get("enterpriseToRevenue"), 2)),
                ("EV/EBITDA", _fmt_number(valuation.get("enterpriseToEbitda"), 2)),
                ("Price/Book", _fmt_number(valuation.get("priceToBook"), 2)),
                ("P/S", _fmt_number(valuation.get("priceToSalesTrailing12Months"), 2)),
                ("Enterprise Value", _fmt_currency(valuation.get("enterpriseValue"), currency, 0)),
                ("FCF Yield", "—"),
            ],
            columns=4,
        )

        metrics_history = timeseries.get("metrics_history", []) if isinstance(timeseries, dict) else []
        _build_line_chart(
            valuation_tab,
            "Bewertungsverlauf (falls verfügbar)",
            {
                "Close": _extract_series(metrics_history, "close"),
                "Volume": _extract_series(metrics_history, "volume"),
            },
        )

        # Risiko & Performance
        bench_var = ctk.StringVar(value="msci_world")
        control = ctk.CTkFrame(risk_tab, fg_color="transparent")
        control.pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(control, text="Benchmark:").pack(side="left", padx=(0, 8))

        bench_choice = ctk.CTkOptionMenu(control, variable=bench_var, values=list(BENCHMARKS.keys()))
        bench_choice.pack(side="left")

        risk_content = ctk.CTkFrame(risk_tab, fg_color="transparent")
        risk_content.pack(fill="both", expand=True)

        def render_risk(_=None):
            for w in risk_content.winfo_children():
                w.destroy()

            benchmark = bench_var.get()
            risk_payload, risk_err = client.load_risk(isin, benchmark)
            compare_payload, comp_err = client.load_benchmark(isin, benchmark)
            ts_payload, ts_err = client.load_timeseries(isin, "price,returns,drawdown,benchmark_relative,benchmark_price", benchmark)

            if risk_err:
                empty_state(risk_content, risk_err)
                return

            risk_metrics = (risk_payload or {}).get("risk", {})
            comparison = (compare_payload or {}).get("comparison", {})
            _kpi_grid(
                risk_content,
                [
                    ("Volatilität", _fmt_percent((risk_metrics.get("volatility") or {}).get("value"))),
                    ("Sharpe", _fmt_number((risk_metrics.get("sharpe_ratio") or {}).get("value"), 2)),
                    ("Drawdown", _fmt_percent((risk_metrics.get("max_drawdown") or {}).get("value"))),
                    ("Beta", _fmt_number((risk_metrics.get("beta") or {}).get("value"), 2)),
                    ("CAGR", _fmt_percent((performance.get("cagr") or {}).get("value"))),
                    ("Total Return", _fmt_percent((performance.get("total_return") or {}).get("value"))),
                    ("Benchmark Return", _fmt_percent((comparison.get("benchmark_total_return") or {}).get("value"))),
                    ("Excess Return", _fmt_percent((comparison.get("excess_return") or {}).get("value"))),
                ],
                columns=4,
            )

            if comp_err or ts_err:
                ctk.CTkLabel(risk_content, text=f"Hinweis: {comp_err or ts_err}", text_color="#ffb347").pack(anchor="w")

            series = (ts_payload or {}).get("series", {})
            _build_line_chart(
                risk_content,
                "Preis und Benchmark",
                {
                    "Instrument": _extract_series(series.get("price", []), "close"),
                    "Benchmark": _extract_series(series.get("benchmark_price", []), "close"),
                },
            )
            _build_line_chart(
                risk_content,
                "Returns / Drawdown / Relative Performance",
                {
                    "Returns": _extract_series(series.get("returns", []), "value"),
                    "Drawdown": _extract_series(series.get("drawdown", []), "value"),
                    "Relativ": _extract_series(series.get("benchmark_relative", []), "value"),
                },
                percent_axis=True,
            )

        bench_choice.configure(command=render_risk)
        render_risk()

        # Analysten
        _kpi_grid(
            analysts_tab,
            [
                ("Empfehlung", _display_value(analysts_payload.get("recommendationKey"))),
                ("Recommendation Mean", _fmt_number(analysts_payload.get("recommendationMean"), 2)),
                ("Analysten", _fmt_number(analysts_payload.get("numberOfAnalystOpinions"), 0)),
                ("Target Mean", _fmt_currency(analysts_payload.get("targetMeanPrice"), currency)),
                ("Target High", _fmt_currency(analysts_payload.get("targetHighPrice"), currency)),
                ("Target Low", _fmt_currency(analysts_payload.get("targetLowPrice"), currency)),
            ],
            columns=3,
        )
        _render_simple_table(analysts_tab, "Earnings Estimates", analysts_payload.get("earnings_estimate", []))
        _render_simple_table(analysts_tab, "Revenue Estimates", analysts_payload.get("revenue_estimate", []))
        _render_simple_table(analysts_tab, "EPS Trend", analysts_payload.get("eps_trend", []))
        _render_simple_table(analysts_tab, "Revisionen", analysts_payload.get("upgrades_downgrades", []))

        # ETF Exposure
        if etf_tab is not None:
            _kpi_grid(
                etf_tab,
                [
                    ("Typ", _display_value(fund_payload.get("quoteType"))),
                    ("Kategorie", _display_value(fund_payload.get("category"))),
                    ("Fund Family", _display_value(fund_payload.get("fundFamily"))),
                    ("Total Assets", _fmt_currency(fund_payload.get("totalAssets"), currency, 0)),
                ],
                columns=4,
            )
            _render_simple_table(etf_tab, "Top Holdings", fund_payload.get("holdings", []))

            sector_weights = fund_payload.get("sectorWeightings", [])
            if isinstance(sector_weights, dict):
                sector_rows = [{"sector": k, "weight": v} for k, v in sector_weights.items()]
            elif isinstance(sector_weights, list):
                sector_rows = sector_weights
            else:
                sector_rows = []
            _render_simple_table(etf_tab, "Sector Weights", sector_rows)
            _render_simple_table(etf_tab, "Asset Allocation / Ratings", [
                {
                    "bondRatings": _display_value(fund_payload.get("bondRatings")),
                    "yield": _display_value(fund_payload.get("yield")),
                    "beta3Year": _display_value(fund_payload.get("beta3Year")),
                    "turnover": _display_value(fund_payload.get("annualHoldingsTurnover")),
                }
            ])

    def on_stock_selected(ev):
        sel_isin = ev.get("isin")
        logger.debug("DepoAnalyse: Instrument ausgewählt ISIN=%s", sel_isin)
        if not sel_isin:
            empty_state(workspace_body, "Ungültige Auswahl: keine ISIN")
            return
        _render_workspace(sel_isin)

    create_depot_pie(top_body, navigator, state, depot_index=depot_index, pick_callback=on_stock_selected)
