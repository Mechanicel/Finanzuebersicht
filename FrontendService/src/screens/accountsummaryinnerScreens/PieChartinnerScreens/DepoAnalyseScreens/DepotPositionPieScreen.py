import logging
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk
import requests
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from finanzuebersicht_shared import get_settings
from src.helpers.UniversalMethoden import clear_ui
from src.models.AppState import AppState
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.analysis_api_client import AnalysisApiClient
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.depot_holdings_helpers import (
    GROUP_BY_OPTIONS,
    UNKNOWN_GROUP_LABEL,
    build_holdings_rows,
    sort_rows,
    summarize_groups,
    with_weight_percent,
)

settings = get_settings()
BACKEND_URL = settings.marketdata_base_url.replace("0.0.0.0", "127.0.0.1").rstrip("/")

logger = logging.getLogger(__name__)


GROUP_LABEL_TO_KEY = {
    "Position": "position",
    "Sektor": "sector",
    "Land": "country",
    "Währung": "currency",
}


def _format_number(value: float, digits: int = 2) -> str:
    return f"{float(value):,.{digits}f}".replace(",", " ")


def _format_money(value: float, currency: str = "EUR") -> str:
    return f"{_format_number(value, 2)} {currency}"


def _resolve_metadata(client: AnalysisApiClient, isin: str) -> dict:
    snapshot, _ = client.load_snapshot(isin)
    full, _ = client.load_full(isin)

    instrument = {}
    profile = {}
    market = {}
    meta = {}

    for payload in (snapshot or {}, full or {}):
        if isinstance(payload.get("instrument"), dict):
            instrument.update(payload.get("instrument"))
        if isinstance(payload.get("profile"), dict):
            profile.update(payload.get("profile"))
        if isinstance(payload.get("market"), dict):
            market.update(payload.get("market"))
        if isinstance(payload.get("meta"), dict):
            meta.update(payload.get("meta"))

    return {
        "name": instrument.get("long_name") or instrument.get("short_name") or instrument.get("symbol"),
        "sector": profile.get("sector") or UNKNOWN_GROUP_LABEL,
        "country": profile.get("country") or UNKNOWN_GROUP_LABEL,
        "currency": market.get("currency") or instrument.get("currency") or "EUR",
        "provider": meta.get("provider"),
        "as_of": meta.get("as_of") or meta.get("asof"),
        "coverage": meta.get("coverage"),
    }


def create_screen(app, navigator, state: AppState, depot_index, pick_callback: callable = None, **kwargs):
    logger.debug("create_screen: Öffne DepotPositionPieScreen für depot_index=%s", depot_index)
    if kwargs.get("clear_before_render", True):
        clear_ui(app)

    person = state.selected_person
    if not person:
        logger.warning("create_screen: Keine Person ausgewählt")
        return

    konten = person.get("Konten", [])
    if depot_index >= len(konten):
        logger.warning("create_screen: depot_index %s außerhalb der Konten-Liste", depot_index)
        return

    konto = konten[depot_index]
    depot_details = konto.get("DepotDetails", [])

    client = AnalysisApiClient(settings.marketdata_base_url)
    now = datetime.now().strftime("%Y-%m-%d")

    price_cache: dict[str, float] = {}
    company_cache: dict[str, str] = {}
    metadata_cache: dict[str, dict] = {}
    holdings_warnings: list[str] = []

    for detail in depot_details:
        isin = str((detail or {}).get("ISIN") or "").strip()
        if not isin:
            continue

        if isin not in price_cache:
            try:
                resp_price = requests.get(f"{BACKEND_URL}/price/{isin}", params={"date": now}, timeout=6)
                resp_price.raise_for_status()
                price_cache[isin] = float(resp_price.json().get("price") or 0.0)
            except Exception as exc:
                logger.error("Preisabruf fehlgeschlagen für %s: %s", isin, exc)
                price_cache[isin] = 0.0
                holdings_warnings.append(f"Preis für {isin} konnte nicht geladen werden (0 angesetzt).")

        if isin not in company_cache:
            try:
                resp_company = requests.get(f"{BACKEND_URL}/company/{isin}", timeout=6)
                resp_company.raise_for_status()
                company_cache[isin] = resp_company.json().get("company_name") or isin
            except Exception as exc:
                logger.error("Company-Abruf fehlgeschlagen für %s: %s", isin, exc)
                company_cache[isin] = isin
                holdings_warnings.append(f"Name für {isin} nicht gefunden (ISIN wird angezeigt).")

        if isin not in metadata_cache:
            metadata_cache[isin] = _resolve_metadata(client, isin)

    rows, helper_warnings = build_holdings_rows(depot_details, price_cache, company_cache, metadata_cache)
    rows = sort_rows(with_weight_percent(rows), key="market_value", reverse=True)
    holdings_warnings.extend(helper_warnings)

    root = ctk.CTkFrame(app, fg_color="transparent")
    root.grid(row=0, column=0, sticky="nsew")
    root.grid_columnconfigure(0, weight=3)
    root.grid_columnconfigure(1, weight=2)
    root.grid_rowconfigure(2, weight=1)

    control_frame = ctk.CTkFrame(root)
    control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(6, 8))
    ctk.CTkLabel(control_frame, text="Gruppieren nach:").pack(side="left", padx=(8, 8), pady=8)

    chart_frame = ctk.CTkFrame(root)
    chart_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 6), pady=(0, 8))
    summary_frame = ctk.CTkFrame(root)
    summary_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 8), pady=(0, 8))
    holdings_frame = ctk.CTkFrame(root)
    holdings_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=8, pady=(0, 8))

    selection_map = {row["isin"]: row for row in rows if row.get("isin")}
    stateful = {"group_by": "position", "summary_rows": []}

    def _emit_selection(isin: str | None):
        if not isin:
            return
        row = selection_map.get(isin, {})
        if pick_callback:
            pick_callback(
                {
                    "event": "stock_selected",
                    "isin": isin,
                    "provider": row.get("provider"),
                    "as_of": row.get("as_of"),
                    "coverage": row.get("coverage"),
                }
            )

    chart_figure = Figure(figsize=(5, 4.2), dpi=100)
    chart_ax = chart_figure.add_subplot(111)
    chart_canvas = FigureCanvasTkAgg(chart_figure, master=chart_frame)
    chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=4, pady=4)

    summary_tree = ttk.Treeview(summary_frame, columns=("group", "value", "weight", "count"), show="headings", height=10)
    summary_tree.heading("group", text="Gruppe")
    summary_tree.heading("value", text="Wert")
    summary_tree.heading("weight", text="Anteil %")
    summary_tree.heading("count", text="#Pos")
    summary_tree.column("group", anchor="w", width=140)
    summary_tree.column("value", anchor="e", width=120)
    summary_tree.column("weight", anchor="e", width=100)
    summary_tree.column("count", anchor="e", width=70)
    summary_tree.pack(fill="both", expand=True, padx=4, pady=4)

    holdings_columns = ("name", "isin", "quantity", "price", "value", "weight", "sector", "country", "currency")
    holdings_tree = ttk.Treeview(holdings_frame, columns=holdings_columns, show="headings", height=12)
    labels = {
        "name": "Name",
        "isin": "ISIN",
        "quantity": "Menge",
        "price": "Preis",
        "value": "Positionswert",
        "weight": "Anteil %",
        "sector": "Sektor",
        "country": "Land",
        "currency": "Währung",
    }
    widths = {"name": 240, "isin": 120, "quantity": 80, "price": 100, "value": 130, "weight": 90, "sector": 130, "country": 110, "currency": 80}

    def _sort_table(column: str, reverse: bool):
        rows_values = [(holdings_tree.set(iid, column), iid) for iid in holdings_tree.get_children("")]

        def _coerce(value: str):
            cleaned = str(value).replace("EUR", "").replace("%", "").replace(" ", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return str(value).lower()

        rows_values.sort(key=lambda item: _coerce(item[0]), reverse=reverse)
        for idx, (_, iid) in enumerate(rows_values):
            holdings_tree.move(iid, "", idx)
        holdings_tree.heading(column, command=lambda: _sort_table(column, not reverse))

    for col in holdings_columns:
        holdings_tree.heading(col, text=labels[col], command=lambda c=col: _sort_table(c, True))
        holdings_tree.column(col, width=widths[col], anchor="w" if col in ("name", "isin", "sector", "country", "currency") else "e")

    tree_scroll_y = ttk.Scrollbar(holdings_frame, orient="vertical", command=holdings_tree.yview)
    tree_scroll_x = ttk.Scrollbar(holdings_frame, orient="horizontal", command=holdings_tree.xview)
    holdings_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
    holdings_tree.grid(row=0, column=0, sticky="nsew")
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    tree_scroll_x.grid(row=1, column=0, sticky="ew")
    holdings_frame.grid_rowconfigure(0, weight=1)
    holdings_frame.grid_columnconfigure(0, weight=1)

    holdings_iid_to_isin: dict[str, str] = {}
    for row in rows:
        iid = holdings_tree.insert(
            "",
            "end",
            values=(
                row.get("name", ""),
                row.get("isin", ""),
                _format_number(row.get("quantity", 0.0), 4),
                _format_money(row.get("price", 0.0), row.get("currency", "EUR")),
                _format_money(row.get("market_value", 0.0), row.get("currency", "EUR")),
                f"{row.get('weight_pct', 0.0):.2f}%",
                row.get("sector", UNKNOWN_GROUP_LABEL),
                row.get("country", UNKNOWN_GROUP_LABEL),
                row.get("currency", "EUR"),
            ),
        )
        holdings_iid_to_isin[iid] = row.get("isin", "")

    _sort_table("value", True)

    def _render_grouped_view():
        group_by = stateful["group_by"]
        summary_rows = summarize_groups(rows, group_by)
        stateful["summary_rows"] = summary_rows

        for item in summary_tree.get_children(""):
            summary_tree.delete(item)

        chart_ax.clear()
        chart_ax.set_title(f"Depot-Aufteilung nach {group_by.title()}")

        if not summary_rows or not any(r.get("value", 0.0) for r in summary_rows):
            chart_ax.text(0.5, 0.5, "Keine Positionen", ha="center", va="center")
            chart_canvas.draw_idle()
            return

        labels_local = [str(item.get("group")) for item in summary_rows]
        values_local = [float(item.get("value") or 0.0) for item in summary_rows]
        wedges, *_ = chart_ax.pie(values_local, labels=labels_local, autopct="%1.1f%%", startangle=90)
        chart_ax.axis("equal")

        for idx, summary in enumerate(summary_rows):
            iid = summary_tree.insert(
                "",
                "end",
                values=(
                    summary.get("group"),
                    _format_money(summary.get("value", 0.0)),
                    f"{float(summary.get('weight_pct') or 0.0):.2f}%",
                    summary.get("count"),
                ),
            )
            summary_tree.set(iid, "group", str(summary.get("group") or UNKNOWN_GROUP_LABEL))

        def _on_pick(event):
            artist = event.artist
            if artist not in wedges:
                return
            idx = wedges.index(artist)
            isins = summary_rows[idx].get("isins") or []
            _emit_selection(isins[0] if isins else None)

        chart_canvas.mpl_disconnect(getattr(chart_canvas, "_dep_pick_id", None) or 0)
        chart_canvas._dep_pick_id = chart_canvas.mpl_connect("pick_event", _on_pick)
        for wedge in wedges:
            wedge.set_picker(True)
        chart_canvas.draw_idle()

    def _on_group_change(label: str):
        stateful["group_by"] = GROUP_LABEL_TO_KEY.get(label, "position")
        if stateful["group_by"] not in GROUP_BY_OPTIONS:
            stateful["group_by"] = "position"
        _render_grouped_view()

    group_selector = ctk.CTkSegmentedButton(control_frame, values=list(GROUP_LABEL_TO_KEY.keys()), command=_on_group_change)
    group_selector.pack(side="left", padx=4, pady=8)
    group_selector.set("Position")

    def _on_holdings_select(_event):
        selection = holdings_tree.selection()
        if not selection:
            return
        _emit_selection(holdings_iid_to_isin.get(selection[0]))

    def _on_summary_select(_event):
        selection = summary_tree.selection()
        if not selection:
            return
        idx = summary_tree.index(selection[0])
        if idx < len(stateful["summary_rows"]):
            isins = stateful["summary_rows"][idx].get("isins") or []
            _emit_selection(isins[0] if isins else None)

    holdings_tree.bind("<<TreeviewSelect>>", _on_holdings_select)
    summary_tree.bind("<<TreeviewSelect>>", _on_summary_select)
    _render_grouped_view()

    if holdings_warnings:
        warning_text = " | ".join(dict.fromkeys(holdings_warnings))
        ctk.CTkLabel(root, text=f"Hinweise: {warning_text}", text_color="#ffb347").grid(
            row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 6)
        )

    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)
