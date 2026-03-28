from __future__ import annotations

from tkinter import ttk
from typing import Any, Callable

import customtkinter as ctk

from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ChartScreen import (
    create_screen as create_chart_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ColumnSelectorScreen import (
    create_column_selector_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.TableScreen import (
    create_screen as create_table_screen,
)
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.ui_helpers import (
    attach_tooltip,
    create_hover_icon_button,
    info_label,
)
from src.ui.components import section_card


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
    if val is None:
        return "—"
    if abs(val) <= 1.0:
        val *= 100.0
    return f"{val:.2f}%"


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


def _metric_value(payload: Any):
    if isinstance(payload, dict):
        return payload.get("value")
    return payload


class OverviewTabController:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.title_var = ctk.StringVar(value="—")
        self.subtitle_var = ctk.StringVar(value="Symbol: — | ISIN: —")
        self.warning_var = ctk.StringVar(value="")

        shell = ctk.CTkFrame(self.frame, fg_color="transparent")
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure((0, 1), weight=1)

        identity_card, identity_body = section_card(shell, "Instrument")
        identity_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=(0, 5))
        ctk.CTkLabel(identity_body, textvariable=self.title_var, font=("Arial", 18, "bold")).pack(anchor="w")
        ctk.CTkLabel(identity_body, textvariable=self.subtitle_var, text_color="gray70").pack(anchor="w", pady=(0, 4))

        grid = ctk.CTkFrame(identity_body, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1), weight=1)
        self.summary_vars: dict[str, ctk.StringVar] = {}
        for idx, key in enumerate(["Aktueller Kurs", "Marktkapitalisierung", "Sektor", "Branche"]):
            row = idx // 2
            col = idx % 2
            box = ctk.CTkFrame(grid)
            box.grid(row=row, column=col, sticky="ew", padx=3, pady=3)
            ctk.CTkLabel(box, text=key, text_color="gray70", font=("Arial", 11)).pack(anchor="w", padx=10, pady=(6, 0))
            self.summary_vars[key] = ctk.StringVar(value="—")
            ctk.CTkLabel(box, textvariable=self.summary_vars[key], font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(0, 6))

        kpi_card, kpi_body = section_card(shell, "KPI-Kompakt")
        kpi_card.grid(row=1, column=0, sticky="nsew", padx=(2, 3), pady=(0, 4))
        kpi_grid = ctk.CTkFrame(kpi_body, fg_color="transparent")
        kpi_grid.pack(fill="x")
        kpi_grid.grid_columnconfigure((0, 1), weight=1)
        self.kpi_vars: dict[str, ctk.StringVar] = {}
        for idx, key in enumerate(["Total Return", "CAGR", "Volatilität", "Sharpe Ratio", "Max Drawdown", "Beta"]):
            row = idx // 2
            col = idx % 2
            box = ctk.CTkFrame(kpi_grid)
            box.grid(row=row, column=col, sticky="ew", padx=3, pady=3)
            ctk.CTkLabel(box, text=key, text_color="gray70", font=("Arial", 10)).pack(anchor="w", padx=8, pady=(5, 0))
            self.kpi_vars[key] = ctk.StringVar(value="—")
            ctk.CTkLabel(box, textvariable=self.kpi_vars[key], font=("Arial", 13, "bold")).pack(anchor="w", padx=8, pady=(0, 5))

        meta_card, meta_body = section_card(shell, "Meta")
        meta_card.grid(row=1, column=1, sticky="nsew", padx=(3, 2), pady=(0, 4))
        self.meta_var = ctk.StringVar(value="Provider: — | As-of: — | Coverage: —")
        ctk.CTkLabel(meta_body, textvariable=self.meta_var, text_color="gray70").pack(anchor="w")

        profile_card, profile_body = section_card(shell, "Profil")
        profile_card.grid(row=2, column=0, columnspan=2, sticky="ew", padx=2)
        self.profile_var = ctk.StringVar(value="Land: — | Währung: — | Börse: —")
        ctk.CTkLabel(profile_body, textvariable=self.profile_var, text_color="gray70").pack(anchor="w")

        self.warning_label = ctk.CTkLabel(self.frame, textvariable=self.warning_var, text_color="#ffb347")

    def update_data(self, isin: str, full_data: dict, metrics: dict, risk: dict):
        instrument = full_data.get("instrument", {}) if isinstance(full_data.get("instrument"), dict) else {}
        market = full_data.get("market", {}) if isinstance(full_data.get("market"), dict) else {}
        profile = full_data.get("profile", {}) if isinstance(full_data.get("profile"), dict) else {}

        name = instrument.get("long_name") or instrument.get("short_name") or instrument.get("symbol") or isin
        self.title_var.set(name)
        self.subtitle_var.set(f"Symbol: {_display_value(instrument.get('symbol'))} | ISIN: {_display_value(instrument.get('isin') or isin)}")

        currency = market.get("currency") or instrument.get("currency") or "EUR"
        self.summary_vars["Aktueller Kurs"].set(_fmt_currency(market.get("currentPrice"), currency))
        self.summary_vars["Marktkapitalisierung"].set(_fmt_currency(market.get("marketCap"), currency, 0))
        self.summary_vars["Sektor"].set(_display_value(profile.get("sector")))
        self.summary_vars["Branche"].set(_display_value(profile.get("industry")))
        self.profile_var.set(
            "Land: {country} | Währung: {currency} | Börse: {exchange}".format(
                country=_display_value(profile.get("country")),
                currency=_display_value(currency),
                exchange=_display_value(instrument.get("exchange")),
            )
        )

        metrics_root = metrics.get("metrics", {}) if isinstance(metrics, dict) else {}
        performance = metrics_root.get("performance", {}) if isinstance(metrics_root, dict) else {}
        risk_root = risk.get("risk", {}) if isinstance(risk, dict) else {}

        self.kpi_vars["Total Return"].set(_fmt_pct(_metric_value(performance.get("total_return"))))
        self.kpi_vars["CAGR"].set(_fmt_pct(_metric_value(performance.get("cagr"))))
        self.kpi_vars["Volatilität"].set(_fmt_pct(_metric_value(risk_root.get("volatility"))))
        self.kpi_vars["Sharpe Ratio"].set(_fmt_number(_metric_value(risk_root.get("sharpe_ratio")), 3))
        self.kpi_vars["Max Drawdown"].set(_fmt_pct(_metric_value(risk_root.get("max_drawdown"))))
        self.kpi_vars["Beta"].set(_fmt_number(_metric_value(risk_root.get("beta")), 3))

        meta = {}
        for source in (full_data.get("meta"), metrics.get("meta"), risk.get("meta")):
            if isinstance(source, dict):
                meta.update({k: v for k, v in source.items() if v not in (None, "")})
        self.meta_var.set(
            f"Provider: {_display_value(meta.get('provider'))} | As-of: {_display_value(meta.get('as_of') or meta.get('asof'))} | Coverage: {_display_value(meta.get('coverage'))}"
        )

    def update_warnings(self, warnings: list[str]):
        if warnings:
            self.warning_var.set("Hinweise: " + " | ".join(warnings))
            if not self.warning_label.winfo_manager():
                self.warning_label.pack(anchor="w", pady=(6, 0))
            return
        self.warning_var.set("")
        if self.warning_label.winfo_manager():
            self.warning_label.pack_forget()

    def update_loading(self, loading: bool):
        return

    def update_selection(self, _isin: str):
        return


class ReturnsTabController:
    def __init__(
        self,
        parent,
        series_options: list[str],
        tooltip_texts: dict[str, str],
        on_series_change: Callable[[list[str]], None],
        on_benchmark_change: Callable[[str | None], None],
        on_group_change: Callable[[str], None],
        on_search: Callable[[], None],
        on_toggle_symbol: Callable[[str, bool], None],
    ):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._on_search = on_search
        self._on_toggle_symbol = on_toggle_symbol
        self._on_series_change = on_series_change
        self._on_group_change = on_group_change
        self._on_benchmark_change = on_benchmark_change

        chart_box, self.chart_body = section_card(self.frame, "Zeitreihen")
        chart_box.pack(fill="both", expand=True, pady=(0, 8))

        controls, controls_body = section_card(self.frame, "Steuerung")
        controls.pack(fill="x", pady=(0, 8))
        benchmark_row = ctk.CTkFrame(controls_body, fg_color="transparent")
        benchmark_row.pack(fill="x", pady=(0, 4))
        info_label(benchmark_row, "Benchmark", tooltip_texts.get("benchmark", "")).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(benchmark_row, text="Segment:").pack(side="left", padx=(0, 6))
        self.group_menu = ctk.CTkOptionMenu(benchmark_row, values=["Alle"], width=170, command=self._on_group_change)
        self.group_menu.pack(side="left", padx=(0, 8))
        self.benchmark_menu = ctk.CTkOptionMenu(benchmark_row, values=["Kein Benchmark"], width=320, command=lambda _: None)
        self.benchmark_menu.pack(side="left")

        series_row = ctk.CTkFrame(controls_body, fg_color="transparent")
        series_row.pack(fill="x")
        ctk.CTkLabel(series_row, text="Serien:").pack(side="left", padx=(0, 6))
        self.selector = create_column_selector_screen(series_row, series_options, callback=self._on_series_change)
        for key, checkbox in self.selector.checkboxes().items():
            if key in tooltip_texts:
                attach_tooltip(checkbox, tooltip_texts[key])

        search_card, search_body = section_card(self.frame, "Freie Vergleiche")
        search_card.pack(fill="x", pady=(8, 0))
        hint_row = ctk.CTkFrame(search_body, fg_color="transparent")
        hint_row.pack(fill="x", pady=(0, 4))
        info_label(
            hint_row,
            "Vergleichssuche",
            tooltip_texts.get(
                "comparison_search",
                "Freie Vergleichswerte ergänzen den Preset-Benchmark aus dem Segment-Menü und bleiben global im Analyse-Screen erhalten.",
            ),
        ).pack(side="left")

        row = ctk.CTkFrame(search_body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 6))
        self.query_var = ctk.StringVar(value="")
        search_entry = ctk.CTkEntry(row, textvariable=self.query_var, placeholder_text="Symbol, Name oder ISIN", height=28)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(row, text="Suchen", width=72, height=28, command=self._on_search).pack(side="left")
        search_entry.bind("<Return>", lambda *_: self._on_search())

        dual_panel = ctk.CTkFrame(search_body, fg_color="transparent")
        dual_panel.pack(fill="x", pady=(0, 4))
        dual_panel.grid_columnconfigure(0, weight=3)
        dual_panel.grid_columnconfigure(1, weight=2)

        self.results_frame = ctk.CTkScrollableFrame(dual_panel, corner_radius=8, height=210)
        self.results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.selected_frame = ctk.CTkScrollableFrame(dual_panel, corner_radius=8, height=210)
        self.selected_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        self.warning_var = ctk.StringVar(value="")
        self.warning_label = ctk.CTkLabel(self.frame, textvariable=self.warning_var, text_color="#ffb347")
        self.loading_var = ctk.StringVar(value="")
        self.loading_label = ctk.CTkLabel(self.frame, textvariable=self.loading_var, text_color="gray70")
        self._chart_signature = None

    def update_data(self, isin: str, ws: dict):
        desired_query = str(ws.get("comparison_last_query") or "")
        if self.query_var.get() != desired_query:
            self.query_var.set(desired_query)

        options = ws.get("benchmark_options") or [("Kein Benchmark", None)]
        groups = ws.get("benchmark_groups") or {"Alle": options[1:]}
        active_group = ws.get("benchmark_active_group") or "Alle"
        group_names = ["Alle", *[name for name in groups.keys() if name != "Alle"]]
        if active_group not in group_names:
            active_group = "Alle"
            ws["benchmark_active_group"] = active_group

        self.group_menu.configure(values=group_names, command=self._on_group_change)
        self.group_menu.set(active_group)

        scoped_options = [("Kein Benchmark", None)] + list(groups.get(active_group) or [])
        labels = [label for label, _ in scoped_options]
        reverse = {label: value for label, value in scoped_options}
        selected_label = next((label for label, value in scoped_options if value == ws.get("benchmark")), "Kein Benchmark")
        self.benchmark_menu.configure(values=labels, command=lambda label: self._on_benchmark_change(reverse.get(label)))
        self.benchmark_menu.set(selected_label)

        selected_set = set(ws.get("selected_series") or [])
        for name, var in self.selector._vars.items():
            var.set(name in selected_set)

        self._render_search_rows(ws)
        payload = ws.get("payloads", {}).get("timeseries_active", {})
        comparison_payload = ws.get("payloads", {}).get("comparison_active", {})
        signature = (
            isin,
            tuple(ws.get("selected_series") or []),
            ws.get("benchmark"),
            id(payload),
            id(comparison_payload),
            tuple(ws.get("warnings", {}).get("timeseries_active", [])),
            tuple(ws.get("warnings", {}).get("comparison_active", [])),
        )
        if signature != self._chart_signature:
            self._chart_signature = signature
            create_chart_screen(
                self.chart_body,
                isin=isin,
                payload=payload,
                warnings=(ws.get("warnings", {}).get("timeseries_active", []) + ws.get("warnings", {}).get("comparison_active", [])),
                selected_series=ws.get("selected_series"),
                benchmark=ws.get("benchmark"),
                comparison_payload=comparison_payload,
            )

    def _render_search_rows(self, ws: dict):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        for widget in self.selected_frame.winfo_children():
            widget.destroy()

        results = ws.get("comparison_search_results") or []
        selected_symbols = {str(entry).upper() for entry in (ws.get("comparison_symbols") or [])}

        ctk.CTkLabel(self.results_frame, text="Suchergebnisse", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 4))
        if not results:
            ctk.CTkLabel(
                self.results_frame,
                text="Suche starten, um Vergleichswerte zu finden.",
                text_color="gray70",
            ).pack(anchor="w", padx=8, pady=(0, 8))
        else:
            for item in results[:14]:
                symbol = str(item.get("symbol") or "").upper()
                if not symbol:
                    continue
                row = ctk.CTkFrame(self.results_frame, corner_radius=8)
                row.pack(fill="x", padx=6, pady=(0, 4))
                already_selected = symbol in selected_symbols
                check = ctk.CTkCheckBox(
                    row,
                    text="",
                    width=20,
                    command=lambda s=symbol, w=None: self._on_toggle_symbol(s, True),
                )
                check.pack(side="left", padx=(8, 6), anchor="n", pady=(8, 0))
                if already_selected:
                    check.select()
                    check.configure(state="disabled")
                else:
                    check.deselect()
                text_box = ctk.CTkFrame(row, fg_color="transparent")
                text_box.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=(6, 6))
                name = item.get("name") or symbol
                line_1 = f"{symbol} · {name}"
                if already_selected:
                    line_1 += "  (bereits gewählt)"
                ctk.CTkLabel(
                    text_box,
                    text=line_1,
                    anchor="w",
                    font=("Arial", 12, "bold"),
                    text_color="gray65" if already_selected else None,
                ).pack(anchor="w")

                meta_parts = []
                isin = item.get("isin")
                exchange = item.get("exchange")
                quote_type = item.get("quote_type")
                currency = item.get("currency")
                region = item.get("region")
                if isin:
                    meta_parts.append(f"ISIN: {isin}")
                if exchange:
                    meta_parts.append(f"Börse: {exchange}")
                if quote_type:
                    meta_parts.append(f"Typ: {quote_type}")
                if currency:
                    meta_parts.append(f"Währung: {currency}")
                if region:
                    meta_parts.append(f"Region: {region}")
                ctk.CTkLabel(
                    text_box,
                    text=" | ".join(meta_parts) if meta_parts else "Keine Zusatzinfos verfügbar",
                    anchor="w",
                    text_color="gray70",
                    font=("Arial", 10),
                ).pack(anchor="w")

        ctk.CTkLabel(self.selected_frame, text="Ausgewählt", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=(8, 4))
        if not selected_symbols:
            ctk.CTkLabel(self.selected_frame, text="Keine freien Vergleichswerte ausgewählt.", text_color="gray70").pack(anchor="w", padx=8, pady=(0, 8))
        for symbol in sorted(selected_symbols):
            row = ctk.CTkFrame(self.selected_frame, corner_radius=8)
            row.pack(fill="x", padx=6, pady=(0, 4))
            ctk.CTkLabel(row, text=symbol, anchor="w").pack(side="left", padx=(8, 0), pady=6)
            remove_btn = create_hover_icon_button(
                row,
                "🗑",
                command=lambda s=symbol: self._on_toggle_symbol(s, False),
                width=22,
                height=20,
                corner_radius=5,
                text_color="gray75",
                hover_text_color="#ff4d4f",
            )
            remove_btn.pack(side="right")

    def update_loading(self, loading: bool, text: str = ""):
        if loading:
            self.loading_var.set(text or "Lade Zeitreihen...")
            if not self.loading_label.winfo_manager():
                self.loading_label.pack(anchor="w", pady=(6, 0))
            return
        if self.loading_label.winfo_manager():
            self.loading_label.pack_forget()

    def update_warnings(self, warnings: list[str]):
        if warnings:
            self.warning_var.set("Hinweise: " + " | ".join(warnings))
            if not self.warning_label.winfo_manager():
                self.warning_label.pack(anchor="w", pady=(8, 0))
            return
        self.warning_var.set("")
        if self.warning_label.winfo_manager():
            self.warning_label.pack_forget()

    def update_selection(self, _isin: str):
        return


class RiskTabController:
    def __init__(self, parent, on_benchmark_change: Callable[[str | None], None], tooltip_texts: dict[str, str]):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._on_benchmark_change = on_benchmark_change
        controls, controls_body = section_card(self.frame, "Benchmark-Auswahl")
        controls.pack(fill="x", pady=(0, 8))
        self.benchmark_menu = ctk.CTkOptionMenu(controls_body, values=["Kein Benchmark"], command=lambda _: None)
        self.benchmark_menu.pack(side="left")

        _, kpi_body = section_card(self.frame, "Risikokennzahlen")
        info_label(kpi_body, "Volatilität / Sharpe / Beta", f"{tooltip_texts.get('volatility', '')} | {tooltip_texts.get('sharpe', '')} | {tooltip_texts.get('beta', '')}").pack(anchor="w", pady=(0, 4))
        self.kpi_vars = {k: ctk.StringVar(value="—") for k in ("Volatilität", "Sharpe Ratio", "Max Drawdown", "Beta")}
        kpi_grid = ctk.CTkFrame(kpi_body, fg_color="transparent")
        kpi_grid.pack(fill="x")
        kpi_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for idx, key in enumerate(self.kpi_vars):
            box = ctk.CTkFrame(kpi_grid)
            box.grid(row=0, column=idx, sticky="ew", padx=4, pady=3)
            ctk.CTkLabel(box, text=key, text_color="gray70", font=("Arial", 10)).pack(anchor="w", padx=8, pady=(5, 0))
            ctk.CTkLabel(box, textvariable=self.kpi_vars[key], font=("Arial", 13, "bold")).pack(anchor="w", padx=8, pady=(0, 5))

        _, cmp_body = section_card(self.frame, "Benchmark-Vergleich")
        self.compare_vars = {k: ctk.StringVar(value="—") for k in ("Company Total Return", "Benchmark Total Return", "Excess Return")}
        cmp_grid = ctk.CTkFrame(cmp_body, fg_color="transparent")
        cmp_grid.pack(fill="x")
        cmp_grid.grid_columnconfigure((0, 1, 2), weight=1)
        for idx, key in enumerate(self.compare_vars):
            box = ctk.CTkFrame(cmp_grid)
            box.grid(row=0, column=idx, sticky="ew", padx=4, pady=3)
            ctk.CTkLabel(box, text=key, text_color="gray70", font=("Arial", 10)).pack(anchor="w", padx=8, pady=(5, 0))
            ctk.CTkLabel(box, textvariable=self.compare_vars[key], font=("Arial", 13, "bold")).pack(anchor="w", padx=8, pady=(0, 5))

        _, self.rel_body = section_card(self.frame, "Relative Benchmark-Zeitreihe")
        self.warning_var = ctk.StringVar(value="")
        self.warning_label = ctk.CTkLabel(self.frame, textvariable=self.warning_var, text_color="#ffb347")
        self.loading_var = ctk.StringVar(value="")
        self.loading_label = ctk.CTkLabel(self.frame, textvariable=self.loading_var, text_color="gray70")
        self._chart_signature = None

    def update_data(self, isin: str, ws: dict):
        options = ws.get("benchmark_options") or [("Kein Benchmark", None)]
        reverse = {label: value for label, value in options}
        selected_label = next((label for label, value in options if value == ws.get("benchmark")), "Kein Benchmark")
        self.benchmark_menu.configure(values=[label for label, _ in options], command=lambda label: self._on_benchmark_change(reverse.get(label)))
        self.benchmark_menu.set(selected_label)

        benchmark = ws.get("benchmark")
        risk_key = f"risk::{benchmark or '_none_'}"
        benchmark_key = f"benchmark::{benchmark or '_none_'}"
        rel_series_key = f"timeseries::risk::{benchmark or '_none_'}"

        risk_payload = ws.get("payloads", {}).get(risk_key, {})
        risk_root = risk_payload.get("risk", {}) if isinstance(risk_payload, dict) else {}
        benchmark_payload = ws.get("payloads", {}).get(benchmark_key, {})

        self.kpi_vars["Volatilität"].set(_fmt_pct(_metric_value(risk_root.get("volatility"))))
        self.kpi_vars["Sharpe Ratio"].set(_fmt_number(_metric_value(risk_root.get("sharpe_ratio")), 3))
        self.kpi_vars["Max Drawdown"].set(_fmt_pct(_metric_value(risk_root.get("max_drawdown"))))
        self.kpi_vars["Beta"].set(_fmt_number(_metric_value(risk_root.get("beta")), 3))

        self.compare_vars["Company Total Return"].set(_fmt_pct(_extract_first(benchmark_payload, ["company_total_return"])))
        self.compare_vars["Benchmark Total Return"].set(_fmt_pct(_extract_first(benchmark_payload, ["benchmark_total_return"])))
        self.compare_vars["Excess Return"].set(_fmt_pct(_extract_first(benchmark_payload, ["excess_return"])))

        rel_payload = ws.get("payloads", {}).get(rel_series_key, {})
        rel_warnings = ws.get("warnings", {}).get(rel_series_key, [])
        signature = (isin, benchmark, id(rel_payload), tuple(rel_warnings))
        if signature != self._chart_signature:
            self._chart_signature = signature
            create_chart_screen(
                self.rel_body,
                isin=isin,
                payload=rel_payload,
                warnings=rel_warnings,
                selected_series=["benchmark_relative"],
                benchmark=benchmark,
            )

    def update_loading(self, loading: bool, text: str = ""):
        if loading:
            self.loading_var.set(text or "Lade Risiko/Benchmark...")
            if not self.loading_label.winfo_manager():
                self.loading_label.pack(anchor="w", pady=(8, 0))
            return
        if self.loading_label.winfo_manager():
            self.loading_label.pack_forget()

    def update_warnings(self, warnings: list[str]):
        if warnings:
            self.warning_var.set("Hinweise: " + " | ".join(warnings))
            if not self.warning_label.winfo_manager():
                self.warning_label.pack(anchor="w", pady=(8, 0))
            return
        self.warning_var.set("")
        if self.warning_label.winfo_manager():
            self.warning_label.pack_forget()

    def update_selection(self, _isin: str):
        return


class FinancialsTabController:
    def __init__(self, parent, on_period_change: Callable[[str], None]):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.on_period_change = on_period_change
        switch_card, switch_body = section_card(self.frame, "Periode")
        switch_card.pack(fill="x", pady=(0, 8))
        self.period_var = ctk.StringVar(value="annual")
        self.period_switch = ctk.CTkSegmentedButton(
            switch_body,
            values=["annual", "quarterly"],
            command=self._handle_period,
        )
        self.period_switch.pack(anchor="w")
        self.period_switch.set("annual")
        self.body = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.body.pack(fill="both", expand=True)

    def _handle_period(self, value: str):
        self.period_var.set(value)
        self.on_period_change(value)

    def clear_body(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    def update_data(self, _isin: str, _ws: dict):
        return

    def update_loading(self, _loading: bool, _text: str = ""):
        return

    def update_warnings(self, _warnings: list[str]):
        return

    def update_selection(self, _isin: str):
        return


class FundamentalsTabController:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._render_signature = None
        self.warning_var = ctk.StringVar(value="")
        self.warning_label = ctk.CTkLabel(self.frame, textvariable=self.warning_var, text_color="#ffb347")

    def update_data(self, _isin: str, payload: dict):
        valuation = payload.get("valuation", {}) if isinstance(payload, dict) else {}
        quality = payload.get("quality", {}) if isinstance(payload, dict) else {}
        growth = payload.get("growth", {}) if isinstance(payload, dict) else {}
        signature = (id(valuation), id(quality), id(growth))
        if signature == self._render_signature:
            return
        self._render_signature = signature
        for widget in self.frame.winfo_children():
            if widget != self.warning_label:
                widget.destroy()
        render_fundamental_section(self.frame, "Valuation", valuation)
        render_fundamental_section(self.frame, "Quality", quality)
        render_fundamental_section(self.frame, "Growth", growth)

    def update_loading(self, _loading: bool, _text: str = ""):
        return

    def update_warnings(self, warnings: list[str]):
        if warnings:
            self.warning_var.set("Hinweise: " + " | ".join(warnings))
            if not self.warning_label.winfo_manager():
                self.warning_label.pack(anchor="w", pady=(8, 0))
            return
        self.warning_var.set("")
        if self.warning_label.winfo_manager():
            self.warning_label.pack_forget()

    def update_selection(self, _isin: str):
        return


class RawTabController:
    def __init__(self, parent):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self._render_signature = None

    def update_data(self, isin: str, payload: dict, warnings: list[str]):
        signature = (isin, id(payload), tuple(warnings))
        if signature == self._render_signature:
            return
        self._render_signature = signature
        create_table_screen(self.frame, isin=isin, payload=payload, warnings=warnings, mode="raw")

    def update_loading(self, _loading: bool, _text: str = ""):
        return

    def update_warnings(self, _warnings: list[str]):
        return

    def update_selection(self, _isin: str):
        return


def render_financial_block(parent, title: str, payload: dict):
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


def render_fundamental_section(parent, title: str, payload: dict):
    _, body = section_card(parent, title)
    rows = []
    for key, value in (payload or {}).items():
        if value in (None, ""):
            continue
        rows.append((key.replace("_", " ").title(), f"{value:,.2f}".replace(",", " ") if isinstance(value, float) else str(value)))
    if not rows:
        ctk.CTkLabel(body, text="Keine Daten verfügbar.", text_color="gray70").pack(anchor="w")
        return
    grid = ctk.CTkFrame(body, fg_color="transparent")
    grid.pack(fill="x")
    grid.grid_columnconfigure((0, 1), weight=1)
    for idx, (label, value) in enumerate(rows):
        box = ctk.CTkFrame(grid)
        box.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=4, pady=4)
        ctk.CTkLabel(box, text=label, text_color="gray70", font=("Arial", 10)).pack(anchor="w", padx=8, pady=(5, 0))
        ctk.CTkLabel(box, text=value, font=("Arial", 13, "bold")).pack(anchor="w", padx=8, pady=(0, 5))
