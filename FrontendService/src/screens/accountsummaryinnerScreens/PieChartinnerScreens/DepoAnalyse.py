import logging
from tkinter import ttk
from typing import Any

import customtkinter as ctk

from finanzuebersicht_shared import get_settings
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ChartScreen import (
    create_screen as create_chart_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ColumnSelectorScreen import (
    create_column_selector_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.TableScreen import (
    create_screen as create_table_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient
from src.ui.components import create_page, empty_state, section_card

logger = logging.getLogger(__name__)
settings = get_settings()

TAB_LABELS = {
    "overview": "Überblick",
    "returns": "Kurs & Rendite",
    "risk": "Risiko & Benchmark",
    "fundamentals": "Fundamentals",
    "financials": "Finanzberichte",
    "raw": "Rohdaten",
}

SERIES_OPTIONS = ["price", "returns", "drawdown", "benchmark_relative", "benchmark_price"]


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


def _fmt_pct(value):
    val = _to_float(value)
    return "—" if val is None else f"{val:.2f}%"


def _display_value(value):
    if value in (None, ""):
        return "—"
    return str(value)


def _extract_first(payload: Any, keys: list[str]):
    if not isinstance(payload, dict):
        return None
    for key in keys:
        if key in payload and payload.get(key) not in (None, ""):
            return payload.get(key)
    return None


def _render_warning_bar(parent, warnings: list[str]):
    if warnings:
        ctk.CTkLabel(parent, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0))


def _metric_card_grid(
    parent,
    items: list[tuple[str, str]],
    columns: int = 3,
    layout: str = "pack",
    row: int | None = None,
    column: int = 0,
    columnspan: int = 1,
    padx=0,
    pady=(2, 6),
    sticky: str = "ew",
):
    grid = ctk.CTkFrame(parent, fg_color="transparent")
    if layout == "grid":
        grid_row = 0 if row is None else row
        grid.grid(row=grid_row, column=column, columnspan=columnspan, padx=padx, pady=pady, sticky=sticky)
    else:
        grid.pack(fill="x", padx=padx, pady=pady)
    for col in range(columns):
        grid.grid_columnconfigure(col, weight=1)

    for idx, (label, value) in enumerate(items):
        card = ctk.CTkFrame(grid, corner_radius=10)
        card.grid(row=idx // columns, column=idx % columns, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(card, text=label, text_color="gray70", font=("Arial", 11)).pack(anchor="w", padx=10, pady=(8, 1))
        ctk.CTkLabel(card, text=value, font=("Arial", 18, "bold")).pack(anchor="w", padx=10, pady=(0, 8))


def _render_snapshot(parent, isin: str, full_data: dict, metrics: dict, risk: dict):
    instrument = full_data.get("instrument", {}) if isinstance(full_data.get("instrument"), dict) else {}
    market = full_data.get("market", {}) if isinstance(full_data.get("market"), dict) else {}
    profile = full_data.get("profile", {}) if isinstance(full_data.get("profile"), dict) else {}

    _, body = section_card(parent, "Header / Snapshot")
    body.grid_columnconfigure((0, 1), weight=1)

    name = instrument.get("long_name") or instrument.get("short_name") or instrument.get("symbol") or isin
    ctk.CTkLabel(body, text=name, font=("Arial", 23, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
    ctk.CTkLabel(
        body,
        text=(
            f"Symbol: {_display_value(instrument.get('symbol'))}   |   "
            f"ISIN: {_display_value(instrument.get('isin') or isin)}"
        ),
        text_color="gray70",
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 8))

    currency = market.get("currency") or instrument.get("currency") or "EUR"
    summary_items = [
        ("Aktueller Kurs", _fmt_currency(market.get("currentPrice"), currency)),
        ("Marktkapitalisierung", _fmt_currency(market.get("marketCap"), currency, 0)),
        ("Ø Volumen", _fmt_number(market.get("averageVolume"), 0)),
        ("Sektor", _display_value(profile.get("sector"))),
        ("Branche", _display_value(profile.get("industry"))),
        ("Land", _display_value(profile.get("country"))),
        ("Website", _display_value(profile.get("website"))),
    ]
    _metric_card_grid(body, summary_items, columns=2, layout="grid", row=2, column=0, columnspan=2)

    kpis = [
        ("Total Return", _fmt_pct(_extract_first(metrics, ["total_return", "totalReturn"]))),
        ("CAGR", _fmt_pct(_extract_first(metrics, ["cagr"]))),
        ("Volatilität", _fmt_pct(_extract_first(risk, ["volatility"]))),
        ("Sharpe Ratio", _fmt_number(_extract_first(risk, ["sharpe_ratio", "sharpe"]), 3)),
        ("Max Drawdown", _fmt_pct(_extract_first(risk, ["max_drawdown"]))),
        ("Beta", _fmt_number(_extract_first(risk, ["beta"]), 3)),
    ]
    kpi_card = ctk.CTkFrame(body, corner_radius=12)
    kpi_card.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    kpi_card.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(kpi_card, text="KPI-Übersicht", font=("Arial", 16, "bold")).grid(
        row=0, column=0, sticky="w", padx=16, pady=(12, 6)
    )
    kpi_body = ctk.CTkFrame(kpi_card, fg_color="transparent")
    kpi_body.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
    _metric_card_grid(kpi_body, kpis, columns=3, layout="grid", row=0, column=0, columnspan=1)

    meta = {}
    for source in (full_data.get("meta"), metrics.get("meta"), risk.get("meta")):
        if isinstance(source, dict):
            meta.update({k: v for k, v in source.items() if v not in (None, "")})

    meta_card = ctk.CTkFrame(body, corner_radius=12)
    meta_card.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    meta_card.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(meta_card, text="Meta / As-of", font=("Arial", 16, "bold")).grid(
        row=0, column=0, sticky="w", padx=16, pady=(12, 6)
    )
    meta_body = ctk.CTkFrame(meta_card, fg_color="transparent")
    meta_body.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
    ctk.CTkLabel(
        meta_body,
        text=(
            f"Provider: {_display_value(meta.get('provider'))}   |   "
            f"As-of: {_display_value(meta.get('as_of') or meta.get('asof'))}   |   "
            f"Coverage: {_display_value(meta.get('coverage'))}"
        ),
        text_color="gray75",
    ).pack(anchor="w")


def _ensure_workspace(registry: dict, isin: str):
    if isin not in registry:
        registry[isin] = {
            "payloads": {},
            "warnings": {},
            "benchmark": None,
            "benchmark_options": None,
            "selected_series": list(SERIES_OPTIONS),
        }
    return registry[isin]


def _load_into(workspace: dict, key: str, loader):
    if key in workspace["payloads"]:
        return
    payload, warning = loader()
    workspace["payloads"][key] = payload or {}
    workspace["warnings"][key] = [warning] if warning else []


def _load_benchmark_catalog(client: AnalysisApiClient, workspace: dict):
    if workspace.get("benchmark_options") is not None:
        return
    payload, warning = client.load_benchmark_catalog()
    items = payload.get("benchmarks") if isinstance(payload, dict) else None
    options: list[tuple[str, str | None]] = [("Kein Benchmark", None)]
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                value = item.get("id") or item.get("symbol") or item.get("code")
                label = item.get("name") or value
                if value:
                    options.append((str(label), str(value)))
            elif item:
                options.append((str(item), str(item)))
    workspace["benchmark_options"] = options
    if warning:
        workspace["warnings"]["benchmark_catalog"] = [warning]


def _series_cache_key(series: list[str], benchmark: str | None):
    return f"timeseries::{','.join(sorted(series))}::{benchmark or '_none_'}"


def _render_fundamental_section(parent, title: str, payload: dict):
    _, body = section_card(parent, title)
    rows = []
    for key, value in (payload or {}).items():
        if value in (None, ""):
            continue
        if isinstance(value, float):
            formatted = f"{value:,.2f}".replace(",", " ")
        else:
            formatted = str(value)
        rows.append((key.replace("_", " ").title(), formatted))

    if not rows:
        ctk.CTkLabel(body, text="Keine Daten verfügbar.", text_color="gray70").pack(anchor="w")
        return

    _metric_card_grid(body, rows, columns=2)


def _render_financial_block(parent, title: str, payload: dict):
    _, body = section_card(parent, title)

    if not isinstance(payload, dict) or not payload:
        ctk.CTkLabel(body, text="Keine Daten verfügbar.", text_color="gray70").pack(anchor="w")
        return

    metrics = sorted({metric for values in payload.values() if isinstance(values, dict) for metric in values.keys()})
    periods = sorted(payload.keys())

    wrapper = ctk.CTkFrame(body)
    wrapper.pack(fill="both", expand=True)

    tree = ttk.Treeview(wrapper, columns=["metric", *periods], show="headings", height=10)
    tree.heading("metric", text="Kennzahl")
    tree.column("metric", width=220, anchor="w", stretch=False)
    for period in periods:
        tree.heading(period, text=period)
        tree.column(period, width=130, anchor="e")

    for metric in metrics:
        values = [metric.replace("_", " ").title()]
        for period in periods:
            val = payload.get(period, {}).get(metric) if isinstance(payload.get(period), dict) else None
            values.append("—" if val in (None, "") else str(val))
        tree.insert("", "end", values=values)

    x_scroll = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
    y_scroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
    tree.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)

    tree.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")
    wrapper.grid_columnconfigure(0, weight=1)
    wrapper.grid_rowconfigure(0, weight=1)


def create_screen(app, navigator, state, depot_index: int = 0, **kwargs):
    ui = create_page(
        app,
        "Depot-Analyse",
        "Analyse-Workspace für Unternehmens- und Wertpapierdaten",
        back_command=lambda: navigator.navigate("AccountSummary", selected_tab="piechart"),
        scrollable=True,
    )
    client = AnalysisApiClient(settings.marketdata_base_url)
    workspace_registry: dict[str, dict] = {}

    _, top_body = section_card(ui["content"], "Depot-Aufteilung", "Klicken Sie auf eine Position, um den Workspace zu laden.")
    method_card = ctk.CTkFrame(top_body)
    method_card.pack(fill="x", pady=(0, 8))
    ctk.CTkLabel(
        method_card,
        text=(
            "Depot-Performance (TWR/MWR) noch nicht implementiert, da im aktuellen Datenmodell "
            "keine belastbare Cashflow-Historie für Ein-/Auszahlungen vorliegt."
        ),
        text_color="#ffb347",
        wraplength=980,
        justify="left",
    ).pack(anchor="w", padx=10, pady=(8, 4))
    provider_meta_var = ctk.StringVar(value="Datenstand: — | Provider: — | Coverage: —")
    ctk.CTkLabel(method_card, textvariable=provider_meta_var, text_color="gray70").pack(anchor="w", padx=10, pady=(0, 8))

    panel_container = ctk.CTkFrame(top_body, fg_color="transparent")
    panel_container.pack(fill="both", expand=True)

    _, workspace_body = section_card(ui["content"], "Analyse-Workspace")

    empty_state(workspace_body, "Bitte oben eine Position auswählen.")

    current = {"isin": None, "tab": "overview"}

    def _active_workspace():
        isin = current["isin"]
        return _ensure_workspace(workspace_registry, isin) if isin else None

    def _load_overview(ws: dict, isin: str):
        _load_into(ws, "company", lambda: client.load_company_analysis(isin))
        _load_into(ws, "metrics", lambda: client.load_metrics(isin))
        _load_into(ws, f"risk::{ws.get('benchmark') or '_none_'}", lambda: client.load_risk(isin, ws.get("benchmark")))

    def _load_timeseries(ws: dict, isin: str):
        key = _series_cache_key(ws["selected_series"], ws.get("benchmark"))
        _load_into(
            ws,
            key,
            lambda: client.load_timeseries(isin, series=",".join(ws["selected_series"]), benchmark=ws.get("benchmark")),
        )
        ws["payloads"]["timeseries_active"] = ws["payloads"].get(key) or {}
        ws["warnings"]["timeseries_active"] = ws["warnings"].get(key, [])

    def _load_risk(ws: dict, isin: str):
        benchmark = ws.get("benchmark")
        _load_into(ws, f"risk::{benchmark or '_none_'}", lambda: client.load_risk(isin, benchmark))
        _load_into(ws, f"benchmark::{benchmark or '_none_'}", lambda: client.load_benchmark(isin, benchmark))
        _load_into(ws, f"timeseries::risk::{benchmark or '_none_'}", lambda: client.load_timeseries(isin, series="benchmark_relative", benchmark=benchmark))

    def _load_fundamentals(ws: dict, isin: str):
        _load_into(ws, "fundamentals", lambda: client.load_fundamentals(isin))
        if not ws["payloads"].get("fundamentals"):
            _load_into(ws, "company", lambda: client.load_company_analysis(isin))

    def _load_financials(ws: dict, isin: str, period: str):
        _load_into(ws, f"financials::{period}", lambda: client.load_financials(isin, period=period))

    def _gather_raw_payload(ws: dict):
        raw = {}
        for key, payload in ws["payloads"].items():
            if payload:
                raw[key] = payload
        return raw

    def _render_tab(tab: str):
        for widget in workspace_body.winfo_children():
            widget.destroy()

        isin = current["isin"]
        if not isin:
            empty_state(workspace_body, "Bitte oben eine Position auswählen.")
            return

        ws = _active_workspace()
        if ws is None:
            return

        _load_benchmark_catalog(client, ws)

        tab_bar = ctk.CTkSegmentedButton(
            workspace_body,
            values=[TAB_LABELS[k] for k in TAB_LABELS],
            command=lambda label: _set_tab(next(key for key, val in TAB_LABELS.items() if val == label)),
        )
        tab_bar.pack(fill="x", pady=(0, 10))
        tab_bar.set(TAB_LABELS[tab])

        content = ctk.CTkFrame(workspace_body, fg_color="transparent")
        content.pack(fill="both", expand=True)

        if tab == "overview":
            _load_overview(ws, isin)
            _render_snapshot(
                content,
                isin,
                ws["payloads"].get("company", {}),
                ws["payloads"].get("metrics", {}),
                ws["payloads"].get(f"risk::{ws.get('benchmark') or '_none_'}", {}),
            )
            _render_warning_bar(content, ws["warnings"].get("company", []) + ws["warnings"].get("metrics", []))
            return

        if tab == "returns":
            controls, controls_body = section_card(content, "Steuerung", "Serienauswahl und Benchmark")
            controls.pack(fill="x", pady=(0, 8))

            ctk.CTkLabel(controls_body, text="Benchmark:").pack(side="left", padx=(0, 8))
            options = ws.get("benchmark_options") or [("Kein Benchmark", None)]
            reverse = {label: value for label, value in options}
            selected_label = next((label for label, value in options if value == ws.get("benchmark")), "Kein Benchmark")

            benchmark_menu = ctk.CTkOptionMenu(
                controls_body,
                values=[label for label, _ in options],
                command=lambda label: _set_benchmark(reverse.get(label)),
            )
            benchmark_menu.set(selected_label)
            benchmark_menu.pack(side="left", padx=(0, 14))

            ctk.CTkLabel(controls_body, text="Serien:").pack(side="left", padx=(0, 6))
            selector = create_column_selector_screen(controls_body, SERIES_OPTIONS, callback=lambda cols: _set_series(cols))
            selected_set = set(ws["selected_series"])
            for name, var in selector._vars.items():
                var.set(name in selected_set)

            chart_box, chart_body = section_card(content, "Zeitreihen")
            chart_box.pack(fill="both", expand=True)
            _load_timeseries(ws, isin)
            create_chart_screen(
                chart_body,
                isin=isin,
                payload=ws["payloads"].get("timeseries_active", {}),
                warnings=ws["warnings"].get("timeseries_active", []),
                selected_series=ws["selected_series"],
                benchmark=ws.get("benchmark"),
            )
            return

        if tab == "risk":
            _load_risk(ws, isin)
            risk_payload = ws["payloads"].get(f"risk::{ws.get('benchmark') or '_none_'}", {})
            benchmark_payload = ws["payloads"].get(f"benchmark::{ws.get('benchmark') or '_none_'}", {})

            options = ws.get("benchmark_options") or [("Kein Benchmark", None)]
            reverse = {label: value for label, value in options}
            selected_label = next((label for label, value in options if value == ws.get("benchmark")), "Kein Benchmark")

            controls, controls_body = section_card(content, "Benchmark-Auswahl")
            controls.pack(fill="x", pady=(0, 8))
            ctk.CTkOptionMenu(
                controls_body,
                values=[label for label, _ in options],
                command=lambda label: _set_benchmark(reverse.get(label)),
            ).pack(side="left")
            controls_body.winfo_children()[-1].set(selected_label)

            _, kpi_body = section_card(content, "Risikokennzahlen")
            _metric_card_grid(
                kpi_body,
                [
                    ("Volatilität", _fmt_pct(_extract_first(risk_payload, ["volatility"]))),
                    ("Sharpe Ratio", _fmt_number(_extract_first(risk_payload, ["sharpe_ratio", "sharpe"]), 3)),
                    ("Max Drawdown", _fmt_pct(_extract_first(risk_payload, ["max_drawdown"]))),
                    ("Beta", _fmt_number(_extract_first(risk_payload, ["beta"]), 3)),
                ],
                columns=4,
            )

            _, cmp_body = section_card(content, "Benchmark-Vergleich")
            _metric_card_grid(
                cmp_body,
                [
                    ("Company Total Return", _fmt_pct(_extract_first(benchmark_payload, ["company_total_return"]))),
                    ("Benchmark Total Return", _fmt_pct(_extract_first(benchmark_payload, ["benchmark_total_return"]))),
                    ("Excess Return", _fmt_pct(_extract_first(benchmark_payload, ["excess_return"]))),
                ],
                columns=3,
            )

            _, rel_body = section_card(content, "Relative Benchmark-Zeitreihe")
            create_chart_screen(
                rel_body,
                isin=isin,
                payload=ws["payloads"].get(f"timeseries::risk::{ws.get('benchmark') or '_none_'}", {}),
                warnings=ws["warnings"].get(f"timeseries::risk::{ws.get('benchmark') or '_none_'}", []),
                selected_series=["benchmark_relative"],
                benchmark=ws.get("benchmark"),
            )
            _render_warning_bar(
                content,
                ws["warnings"].get(f"risk::{ws.get('benchmark') or '_none_'}", [])
                + ws["warnings"].get(f"benchmark::{ws.get('benchmark') or '_none_'}", []),
            )
            return

        if tab == "fundamentals":
            _load_fundamentals(ws, isin)
            payload = ws["payloads"].get("fundamentals", {})
            if not payload:
                company = ws["payloads"].get("company", {})
                payload = {
                    "valuation": company.get("valuation", {}),
                    "quality": company.get("quality", {}),
                    "growth": company.get("growth", {}),
                }

            _render_fundamental_section(content, "Valuation", payload.get("valuation", {}))
            _render_fundamental_section(content, "Quality", payload.get("quality", {}))
            _render_fundamental_section(content, "Growth", payload.get("growth", {}))
            _render_warning_bar(content, ws["warnings"].get("fundamentals", []))
            return

        if tab == "financials":
            switch_card, switch_body = section_card(content, "Periode")
            switch_card.pack(fill="x", pady=(0, 8))

            period_var = ctk.StringVar(value="annual")

            def _reload_financials(*_):
                period = period_var.get()
                _load_financials(ws, isin, period)
                payload = ws["payloads"].get(f"financials::{period}", {})
                for widget in financial_area.winfo_children():
                    widget.destroy()
                _render_financial_block(financial_area, "Income Statement", payload.get("income_statement", {}))
                _render_financial_block(financial_area, "Balance Sheet", payload.get("balance_sheet", {}))
                _render_financial_block(financial_area, "Cash Flow", payload.get("cash_flow", {}))
                _render_warning_bar(financial_area, ws["warnings"].get(f"financials::{period}", []))

            ctk.CTkSegmentedButton(
                switch_body,
                values=["annual", "quarterly"],
                command=lambda value: (period_var.set(value), _reload_financials()),
            ).pack(anchor="w")
            switch_body.winfo_children()[-1].set("annual")

            financial_area = ctk.CTkFrame(content, fg_color="transparent")
            financial_area.pack(fill="both", expand=True)
            _reload_financials()
            return

        if tab == "raw":
            _load_overview(ws, isin)
            _load_fundamentals(ws, isin)
            _load_risk(ws, isin)
            _load_financials(ws, isin, "annual")
            raw_payload = _gather_raw_payload(ws)
            create_table_screen(
                content,
                isin=isin,
                payload=raw_payload,
                warnings=sum(ws["warnings"].values(), []),
                mode="raw",
            )

    def _set_tab(tab: str):
        current["tab"] = tab
        _render_tab(tab)

    def _set_benchmark(benchmark: str | None):
        ws = _active_workspace()
        if ws is None:
            return
        if ws.get("benchmark") == benchmark:
            return
        ws["benchmark"] = benchmark
        _render_tab(current["tab"])

    def _set_series(columns: list[str]):
        ws = _active_workspace()
        if ws is None:
            return
        ws["selected_series"] = columns or ["price"]
        if current["tab"] == "returns":
            _render_tab("returns")

    def on_stock_selected(ev):
        sel_isin = ev.get("isin")
        logger.debug("DepoAnalyse: Instrument ausgewählt ISIN=%s", sel_isin)
        if not sel_isin:
            empty_state(workspace_body, "Ungültige Auswahl: keine ISIN")
            return

        provider_meta_var.set(
            "Datenstand: {as_of} | Provider: {provider} | Coverage: {coverage}".format(
                as_of=ev.get("as_of") or "—",
                provider=ev.get("provider") or "—",
                coverage=ev.get("coverage") or "—",
            )
        )

        current["isin"] = sel_isin
        current["tab"] = "overview"
        _ensure_workspace(workspace_registry, sel_isin)
        _render_tab("overview")

    create_depot_pie(panel_container, navigator, state, depot_index=depot_index, pick_callback=on_stock_selected, clear_before_render=False)
