import logging
import time
from typing import Any

import customtkinter as ctk

from finanzuebersicht_shared import get_settings
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.DepotPositionPieScreen import (
    create_screen as create_depot_pie,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.TableScreen import (
    create_screen as create_table_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.tab_controllers import (
    FinancialsTabController,
    OverviewTabController,
    ReturnsTabController,
    RiskTabController,
    render_financial_block,
    render_fundamental_section,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient
from src.ui.background_loader import run_in_background
from src.ui.components import create_page, empty_state, section_card

logger = logging.getLogger(__name__)
performance_logger = logging.getLogger("performance")
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

TOOLTIP_TEXTS = {
    "benchmark": "Vergleichsindex oder ETF-Proxy als Referenzmaßstab.",
    "benchmark_relative": "Relative Entwicklung der Aktie gegenüber dem gewählten Benchmark.",
    "benchmark_price": "Kursverlauf des Benchmark-Instruments.",
    "drawdown": "Prozentualer Rückgang vom jeweils vorherigen Hochpunkt.",
    "returns": "Kumulierte Rendite aus der Kursentwicklung über den Zeitraum.",
    "beta": "Sensitivität zum Benchmark (1.0 = bewegt sich ähnlich).",
    "sharpe": "Rendite im Verhältnis zum eingegangenen Risiko (höher ist besser).",
    "volatility": "Schwankungsbreite der Renditen auf Jahresbasis.",
}


def _ensure_workspace(registry: dict, isin: str):
    if isin not in registry:
        registry[isin] = {
            "payloads": {},
            "warnings": {},
            "benchmark": None,
            "benchmark_options": None,
            "benchmark_groups": None,
            "benchmark_active_group": "Alle",
            "selected_series": list(SERIES_OPTIONS),
            "comparison_symbols": [],
            "comparison_search_results": [],
            "request_generation": {},
            "loading": {},
            "benchmark_catalog_loading": False,
            "benchmark_catalog_loaded": False,
            "benchmark_catalog_callbacks": [],
        }
    return registry[isin]


def _load_into(workspace: dict, key: str, loader):
    if key in workspace["payloads"]:
        return
    payload, warning = loader()
    workspace["payloads"][key] = payload or {}
    workspace["warnings"][key] = [warning] if warning else []


def _series_cache_key(series: list[str], benchmark: str | None):
    return f"timeseries::{','.join(sorted(series))}::{benchmark or '_none_'}"


def _comparison_cache_key(symbols: list[str]):
    normalized = sorted({str(symbol).upper() for symbol in (symbols or []) if symbol})
    return f"comparison::{','.join(normalized) if normalized else '_none_'}"


def _next_generation(ws: dict, key: str) -> int:
    generation = int(ws["request_generation"].get(key, 0)) + 1
    ws["request_generation"][key] = generation
    return generation


def create_screen(app, navigator, state, depot_index: int = 0, **kwargs):
    create_started = time.perf_counter()
    if settings.performance_logging:
        performance_logger.info("DepoAnalyse.create_screen started (depot_index=%s)", depot_index)

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

    current = {"isin": None, "tab": "overview"}
    ui_state: dict[str, Any] = {
        "tab_bar": None,
        "tabs_host": None,
        "empty_box": None,
        "tab_frames": {},
        "controllers": {},
    }

    def _active_workspace():
        isin = current["isin"]
        return _ensure_workspace(workspace_registry, isin) if isin else None

    def _set_loading(ws: dict, area: str, active: bool):
        ws["loading"][area] = active

    def _show_warning(frame, warnings: list[str]):
        if not warnings:
            return
        ctk.CTkLabel(frame, text="Hinweise: " + " | ".join(warnings), text_color="#ffb347").pack(anchor="w", pady=(8, 0))

    def _ensure_shell():
        if ui_state["tab_bar"] is not None:
            return
        ui_state["empty_box"] = empty_state(workspace_body, "Bitte oben eine Position auswählen.")
        ui_state["tab_bar"] = ctk.CTkSegmentedButton(
            workspace_body,
            values=[TAB_LABELS[k] for k in TAB_LABELS],
            command=lambda label: _set_tab(next(key for key, val in TAB_LABELS.items() if val == label)),
        )
        ui_state["tabs_host"] = ctk.CTkFrame(workspace_body, fg_color="transparent")
        ui_state["tabs_host"].grid_columnconfigure(0, weight=1)
        ui_state["tabs_host"].grid_rowconfigure(0, weight=1)

    def _show_empty():
        _ensure_shell()
        ui_state["tab_bar"].pack_forget()
        ui_state["tabs_host"].pack_forget()
        if not ui_state["empty_box"].winfo_manager():
            ui_state["empty_box"].pack(fill="x", pady=10)

    def _show_shell():
        _ensure_shell()
        ui_state["empty_box"].pack_forget()
        if not ui_state["tab_bar"].winfo_manager():
            ui_state["tab_bar"].pack(fill="x", pady=(0, 10))
        if not ui_state["tabs_host"].winfo_manager():
            ui_state["tabs_host"].pack(fill="both", expand=True)

    def _get_tab_frame(tab: str):
        frame = ui_state["tab_frames"].get(tab)
        if frame is None:
            frame = ctk.CTkFrame(ui_state["tabs_host"], fg_color="transparent")
            frame.grid(row=0, column=0, sticky="nsew")
            ui_state["tab_frames"][tab] = frame
        return frame

    def _ensure_controllers():
        controllers = ui_state["controllers"]
        if controllers:
            return

        controllers["overview"] = OverviewTabController(_get_tab_frame("overview"))
        controllers["overview"].frame.pack(fill="both", expand=True)

        controllers["returns"] = ReturnsTabController(
            _get_tab_frame("returns"),
            series_options=SERIES_OPTIONS,
            tooltip_texts=TOOLTIP_TEXTS,
            on_series_change=_set_series,
            on_benchmark_change=_set_benchmark,
            on_group_change=lambda g: _on_benchmark_group_change(g),
            on_search=_run_returns_search,
            on_toggle_symbol=_toggle_comparison_symbol,
        )
        controllers["returns"].frame.pack(fill="both", expand=True)

        controllers["risk"] = RiskTabController(_get_tab_frame("risk"), on_benchmark_change=_set_benchmark, tooltip_texts=TOOLTIP_TEXTS)
        controllers["risk"].frame.pack(fill="both", expand=True)

        controllers["financials"] = FinancialsTabController(_get_tab_frame("financials"), on_period_change=_reload_financials)
        controllers["financials"].frame.pack(fill="both", expand=True)

    def _show_tab(tab: str):
        _show_shell()
        _ensure_controllers()
        ui_state["tab_bar"].set(TAB_LABELS[tab])
        _get_tab_frame(tab).tkraise()

    def _load_overview(ws: dict, isin: str):
        _load_into(ws, "company", lambda: client.load_company_analysis(isin))
        _load_into(ws, "metrics", lambda: client.load_metrics(isin))
        _load_into(ws, f"risk::{ws.get('benchmark') or '_none_'}", lambda: client.load_risk(isin, ws.get("benchmark")))

    def _ensure_benchmark_catalog_async(ws: dict, callback=None):
        if ws.get("benchmark_catalog_loaded") or ws.get("benchmark_options") is not None:
            ws["benchmark_catalog_loaded"] = True
            if callback:
                callback()
            return
        if callback:
            ws["benchmark_catalog_callbacks"].append(callback)
        if ws.get("benchmark_catalog_loading"):
            return

        ws["benchmark_catalog_loading"] = True
        generation = _next_generation(ws, "benchmark_catalog")

        def _worker():
            return client.load_benchmark_catalog()

        def _done(result):
            if ws["request_generation"].get("benchmark_catalog") != generation:
                return
            ws["benchmark_catalog_loading"] = False
            payload, warning = result
            catalog = payload.get("benchmarks") if isinstance(payload, dict) else None
            items = catalog.get("items") if isinstance(catalog, dict) and isinstance(catalog.get("items"), dict) else {}
            groups_payload = catalog.get("groups") if isinstance(catalog, dict) and isinstance(catalog.get("groups"), dict) else {}

            options: list[tuple[str, str | None]] = [("Kein Benchmark", None)]
            for key, item in items.items():
                label = item.get("name") if isinstance(item, dict) else key
                options.append((str(label or key), str(key)))

            grouped_options: dict[str, list[tuple[str, str | None]]] = {"Alle": options[1:]}
            for segment, entries in groups_payload.items():
                if not isinstance(entries, list):
                    continue
                segment_options = []
                for entry in entries:
                    if not isinstance(entry, dict) or not entry.get("key"):
                        continue
                    segment_options.append((str(entry.get("name") or entry.get("key")), str(entry.get("key"))))
                if segment_options:
                    grouped_options[str(segment)] = segment_options

            ws["benchmark_options"] = options
            ws["benchmark_groups"] = grouped_options
            default_key = payload.get("default") if isinstance(payload, dict) else None
            if ws.get("benchmark") is None and default_key:
                ws["benchmark"] = str(default_key)
            if warning:
                ws["warnings"]["benchmark_catalog"] = [warning]
            ws["benchmark_catalog_loaded"] = True
            callbacks = list(ws.get("benchmark_catalog_callbacks") or [])
            ws["benchmark_catalog_callbacks"].clear()
            for cb in callbacks:
                cb()

        run_in_background(app, _worker, _done)

    def _refresh_overview():
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        _show_tab("overview")
        _load_overview(ws, isin)
        risk_key = f"risk::{ws.get('benchmark') or '_none_'}"
        controller: OverviewTabController = ui_state["controllers"]["overview"]
        controller.update_data(isin, ws["payloads"].get("company", {}), ws["payloads"].get("metrics", {}), ws["payloads"].get(risk_key, {}))
        controller.update_warnings(ws["warnings"].get("company", []) + ws["warnings"].get("metrics", []))

    def _refresh_returns():
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        _show_tab("returns")
        controller: ReturnsTabController = ui_state["controllers"]["returns"]
        _ensure_benchmark_catalog_async(ws, callback=lambda: current["isin"] == isin and controller.update_data(isin, ws))

        benchmark = ws.get("benchmark")
        series_key = _series_cache_key(list(ws["selected_series"]), benchmark)
        symbols = ws.get("comparison_symbols") or []
        comparison_key = _comparison_cache_key(symbols)

        has_series_cache = series_key in ws["payloads"]
        has_comparison_cache = not symbols or comparison_key in ws["payloads"]

        if has_series_cache:
            ws["payloads"]["timeseries_active"] = ws["payloads"].get(series_key) or {}
            ws["warnings"]["timeseries_active"] = ws["warnings"].get(series_key, [])
        if has_comparison_cache:
            ws["payloads"]["comparison_active"] = ws["payloads"].get(comparison_key) or {}
            ws["warnings"]["comparison_active"] = ws["warnings"].get(comparison_key, [])

        controller.update_data(isin, ws)
        controller.update_warnings(ws["warnings"].get("timeseries_active", []) + ws["warnings"].get("comparison_active", []) + ws["warnings"].get("comparison_search", []))
        if has_series_cache and has_comparison_cache:
            controller.update_loading(False)
            return

        controller.update_loading(True, "Lade Zeitreihen...")
        _set_loading(ws, "returns_chart", True)
        generation = _next_generation(ws, "returns_chart")

        def _worker():
            result = {}
            if not has_series_cache:
                result["series"] = client.load_timeseries(isin, series=",".join(ws["selected_series"]), benchmark=benchmark)
            if not has_comparison_cache and symbols:
                result["comparison"] = client.load_comparison_timeseries(isin, symbols)
            return result

        def _done(result):
            if ws["request_generation"].get("returns_chart") != generation:
                return
            if "series" in result:
                payload, warning = result["series"]
                ws["payloads"][series_key] = payload or {}
                ws["warnings"][series_key] = [warning] if warning else []
            if "comparison" in result:
                payload, warning = result["comparison"]
                ws["payloads"][comparison_key] = payload or {}
                ws["warnings"][comparison_key] = [warning] if warning else []
            ws["payloads"]["timeseries_active"] = ws["payloads"].get(series_key) or {}
            ws["warnings"]["timeseries_active"] = ws["warnings"].get(series_key, [])
            ws["payloads"]["comparison_active"] = ws["payloads"].get(comparison_key) or {}
            ws["warnings"]["comparison_active"] = ws["warnings"].get(comparison_key, [])
            _set_loading(ws, "returns_chart", False)
            if current["tab"] == "returns" and current["isin"] == isin:
                controller.update_data(isin, ws)
                controller.update_loading(False)
                controller.update_warnings(ws["warnings"].get("timeseries_active", []) + ws["warnings"].get("comparison_active", []) + ws["warnings"].get("comparison_search", []))

        run_in_background(app, _worker, _done)

    def _refresh_risk():
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        _show_tab("risk")
        controller: RiskTabController = ui_state["controllers"]["risk"]
        _ensure_benchmark_catalog_async(ws, callback=lambda: current["isin"] == isin and controller.update_data(isin, ws))

        benchmark = ws.get("benchmark")
        risk_key = f"risk::{benchmark or '_none_'}"
        benchmark_key = f"benchmark::{benchmark or '_none_'}"
        rel_series_key = f"timeseries::risk::{benchmark or '_none_'}"
        has_cache = all(key in ws["payloads"] for key in (risk_key, benchmark_key, rel_series_key))

        controller.update_data(isin, ws)
        controller.update_warnings(ws["warnings"].get(risk_key, []) + ws["warnings"].get(benchmark_key, []))
        if has_cache:
            controller.update_loading(False)
            return

        controller.update_loading(True, "Lade Risiko/Benchmark...")
        _set_loading(ws, "risk_panel", True)
        generation = _next_generation(ws, "risk_panel")

        def _worker():
            return {
                "risk": client.load_risk(isin, benchmark),
                "benchmark": client.load_benchmark(isin, benchmark),
                "relative": client.load_timeseries(isin, series="benchmark_relative", benchmark=benchmark),
            }

        def _done(result):
            if ws["request_generation"].get("risk_panel") != generation:
                return
            risk_payload, risk_warning = result["risk"]
            benchmark_payload, benchmark_warning = result["benchmark"]
            relative_payload, relative_warning = result["relative"]
            ws["payloads"][risk_key] = risk_payload or {}
            ws["warnings"][risk_key] = [risk_warning] if risk_warning else []
            ws["payloads"][benchmark_key] = benchmark_payload or {}
            ws["warnings"][benchmark_key] = [benchmark_warning] if benchmark_warning else []
            ws["payloads"][rel_series_key] = relative_payload or {}
            ws["warnings"][rel_series_key] = [relative_warning] if relative_warning else []
            _set_loading(ws, "risk_panel", False)
            if current["tab"] == "risk" and current["isin"] == isin:
                controller.update_data(isin, ws)
                controller.update_loading(False)
                controller.update_warnings(ws["warnings"].get(risk_key, []) + ws["warnings"].get(benchmark_key, []))

        run_in_background(app, _worker, _done)

    def _refresh_fundamentals():
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        _show_tab("fundamentals")
        frame = _get_tab_frame("fundamentals")
        for w in frame.winfo_children():
            w.destroy()
        _load_into(ws, "fundamentals", lambda: client.load_fundamentals(isin))
        if not ws["payloads"].get("fundamentals"):
            _load_into(ws, "company", lambda: client.load_company_analysis(isin))
            company = ws["payloads"].get("company", {})
            payload = {
                "valuation": company.get("valuation", {}),
                "quality": company.get("quality", {}),
                "growth": company.get("growth", {}),
            }
        else:
            payload = ws["payloads"].get("fundamentals", {})
        render_fundamental_section(frame, "Valuation", payload.get("valuation", {}))
        render_fundamental_section(frame, "Quality", payload.get("quality", {}))
        render_fundamental_section(frame, "Growth", payload.get("growth", {}))
        _show_warning(frame, ws["warnings"].get("fundamentals", []))

    def _reload_financials(period: str):
        if current["tab"] != "financials":
            return
        _refresh_financials(period)

    def _refresh_financials(period: str | None = None):
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        _show_tab("financials")
        controller: FinancialsTabController = ui_state["controllers"]["financials"]
        selected_period = period or controller.period_var.get()
        controller.period_switch.set(selected_period)
        controller.clear_body()
        ctk.CTkLabel(controller.body, text="Lade Finanzberichte...", text_color="gray70").pack(anchor="w")
        key = f"financials::{selected_period}"

        def _render_payload():
            controller.clear_body()
            payload = ws["payloads"].get(key, {})
            render_financial_block(controller.body, "Income Statement", payload.get("income_statement", {}))
            render_financial_block(controller.body, "Balance Sheet", payload.get("balance_sheet", {}))
            render_financial_block(controller.body, "Cash Flow", payload.get("cash_flow", {}))
            _show_warning(controller.body, ws["warnings"].get(key, []))

        if key in ws["payloads"]:
            _render_payload()
            return

        generation = _next_generation(ws, "financials")

        def _worker():
            return client.load_financials(isin, period=selected_period)

        def _done(result):
            if ws["request_generation"].get("financials") != generation:
                return
            payload, warning = result
            ws["payloads"][key] = payload or {}
            ws["warnings"][key] = [warning] if warning else []
            if current["tab"] == "financials" and current["isin"] == isin and controller.period_var.get() == selected_period:
                _render_payload()

        run_in_background(app, _worker, _done)

    def _refresh_raw():
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        _show_tab("raw")
        frame = _get_tab_frame("raw")
        for w in frame.winfo_children():
            w.destroy()
        _load_overview(ws, isin)
        _load_into(ws, "fundamentals", lambda: client.load_fundamentals(isin))
        benchmark = ws.get("benchmark")
        _load_into(ws, f"benchmark::{benchmark or '_none_'}", lambda: client.load_benchmark(isin, benchmark))
        _load_into(ws, "financials::annual", lambda: client.load_financials(isin, period="annual"))

        raw_payload = {k: v for k, v in ws["payloads"].items() if v}
        create_table_screen(frame, isin=isin, payload=raw_payload, warnings=sum(ws["warnings"].values(), []), mode="raw")

    def _refresh_tab(tab: str):
        if tab == "overview":
            _refresh_overview()
        elif tab == "returns":
            _refresh_returns()
        elif tab == "risk":
            _refresh_risk()
        elif tab == "fundamentals":
            _refresh_fundamentals()
        elif tab == "financials":
            _refresh_financials()
        elif tab == "raw":
            _refresh_raw()

    def _set_tab(tab: str):
        current["tab"] = tab
        if current["isin"]:
            _refresh_tab(tab)

    def _set_benchmark(benchmark: str | None):
        ws = _active_workspace()
        if ws is None:
            return
        if ws.get("benchmark") == benchmark:
            return
        ws["benchmark"] = benchmark
        if current["tab"] in {"overview", "returns", "risk", "raw"} and current["isin"]:
            _refresh_tab(current["tab"])

    def _set_series(columns: list[str]):
        ws = _active_workspace()
        if ws is None:
            return
        ws["selected_series"] = columns or ["price"]
        if current["tab"] == "returns" and current["isin"]:
            _refresh_returns()

    def _on_benchmark_group_change(group: str | None = None):
        ws = _active_workspace()
        if ws is None:
            return
        ws["benchmark_active_group"] = group or "Alle"
        if current["tab"] == "returns" and current["isin"]:
            ui_state["controllers"]["returns"].update_data(current["isin"], ws)

    def _toggle_comparison_symbol(symbol: str, selected: bool):
        ws = _active_workspace()
        if ws is None:
            return
        normalized = (symbol or "").strip().upper()
        if not normalized:
            return
        current_symbols = list(ws.get("comparison_symbols") or [])
        symbol_set = {entry.upper() for entry in current_symbols}
        if selected and normalized not in symbol_set:
            current_symbols.append(normalized)
        if not selected:
            current_symbols = [entry for entry in current_symbols if entry.upper() != normalized]
        ws["comparison_symbols"] = list(dict.fromkeys(current_symbols))
        if current["tab"] == "returns" and current["isin"]:
            _refresh_returns()

    def _run_returns_search():
        ws = _active_workspace()
        isin = current["isin"]
        if ws is None or not isin:
            return
        controller: ReturnsTabController = ui_state["controllers"]["returns"]
        query = controller.query_var.get().strip()
        results, search_warning = client.search_benchmark_candidates(query)
        ws["comparison_search_results"] = list((results or {}).get("results") or [])
        ws["warnings"]["comparison_search"] = [search_warning] if search_warning else []
        if current["tab"] == "returns":
            controller.update_data(isin, ws)
            controller.update_warnings(ws["warnings"].get("timeseries_active", []) + ws["warnings"].get("comparison_active", []) + ws["warnings"].get("comparison_search", []))

    def on_stock_selected(ev):
        selection_started = time.perf_counter()
        sel_isin = ev.get("isin")
        if not sel_isin:
            _show_empty()
            return

        provider_meta_var.set(
            "Datenstand: {as_of} | Provider: {provider} | Coverage: {coverage}".format(
                as_of=ev.get("as_of") or "—",
                provider=ev.get("provider") or "—",
                coverage=ev.get("coverage") or "—",
            )
        )

        current["isin"] = sel_isin
        _ensure_workspace(workspace_registry, sel_isin)
        _refresh_tab(current["tab"])
        if settings.performance_logging:
            performance_logger.info(
                "DepoAnalyse workspace render for %s took %.2fs", sel_isin, time.perf_counter() - selection_started
            )

    _show_empty()
    create_depot_pie(
        panel_container,
        navigator,
        state,
        depot_index=depot_index,
        pick_callback=on_stock_selected,
        api_client=client,
        clear_before_render=False,
    )
    if settings.performance_logging:
        performance_logger.info("DepoAnalyse.create_screen finished in %.2fs", time.perf_counter() - create_started)
