import customtkinter as ctk
import logging
from src.helpers.UniversalMethoden import clear_ui
from src.models import AppState

from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.InfoScreen import create_info_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.CalendarScreen import create_calendar_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.PriceTargetsScreen import create_price_targets_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.QuarterlyIncomeScreen import create_quarterly_income_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.HistoryScreen import create_history_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.OptionChainScreen import create_option_chain_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.AnnualFinancialsScreen import create_annual_financials_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.BalanceSheetScreen import create_balance_sheet_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.CashflowScreen import create_cashflow_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.AktienAnalyseScreens.EarningsScreen import create_earnings_screen
from src.screens.accountsummaryinnerScreens.PieChartinnerScreens.DepoAnalyseScreens.ColumnSelectorScreen import create_column_selector_screen

logger = logging.getLogger(__name__)

def create_screen(app, navigator, state: AppState, isin: str = None, column_frame=None, **kwargs):
    clear_ui(app)

    if not isin:
        ctk.CTkLabel(app, text="Keine Aktie ausgewählt").pack(pady=20)
        return

    infos = state.stock_data_manager.get_stock_info(isin)
    if infos.get("error") and len(infos) == 1:
        ctk.CTkLabel(app, text=f"Fehler: {infos['error']}", text_color="red").pack(pady=20)
        return

    container = ctk.CTkFrame(app, fg_color="transparent")
    container.pack(fill="both", expand=True, padx=20, pady=10)
    ctk.CTkLabel(
        container,
        text=f"Aktien-Kennzahlen für ISIN {isin}",
        font=("Arial", 16, "bold")
    ).pack(pady=(0,10))
    if infos.get("error"):
        ctk.CTkLabel(container, text=f"Warnung: {infos['error']}", text_color="orange")\
           .pack(pady=(0,10))

    # Tabs und Daten-Quellen
    tab_map = {
        "info":              (create_info_screen,             infos.get("info", {})),
        "calendar":          (create_calendar_screen,         infos.get("calendar", {})),
        "price_targets":     (create_price_targets_screen,    infos.get("price_targets", {})),
        "quarterly_income":  (create_quarterly_income_screen, infos.get("quarterly_income_stmt", [])),
        "history":           (create_history_screen,          infos.get("history_20y", [])),
        "option_chain":      (create_option_chain_screen,     infos.get("option_chain", {})),
        "annual_financials": (create_annual_financials_screen,infos.get("annual_financials", {})),
        "balance_sheet":     (create_balance_sheet_screen,    infos.get("balance_sheet", {})),
        "cashflow":          (create_cashflow_screen,         infos.get("cashflow", {})),
        "earnings":          (create_earnings_screen,         infos.get("earnings", [])),
    }
    built = set()

    def _on_tab_changed(*_):
        tab = tabs.get()
        func, data = tab_map[tab]
        frame = tabs.tab(tab)
        logger.debug("Wechsle zu Tab '%s'", tab)

        # Inhalt nur einmalig bauen
        if tab not in built:
            clear_ui(frame)
            try:
                func(frame, data)
            except Exception as e:
                logger.exception("Fehler in Tab %s: %s", tab, e)
                ctk.CTkLabel(frame, text="Daten konnten nicht dargestellt werden", text_color="red")\
                   .pack(pady=20)
            built.add(tab)

        # Column-Selector bei list-of-dict
        if column_frame and isinstance(data, list) and data and isinstance(data[0], dict):
            clear_ui(column_frame)
            cols = list(data[0].keys())
            logger.debug("Erstelle Column-Selector für Keys: %s", cols)
            vis = {c: True for c in cols}

            def on_col(col, show):
                vis[col] = show
                filt = []
                for rec in data:
                    row = {}
                    for c in cols:
                        if vis[c]:
                            row[c] = rec.get(c)
                    filt.append(row)
                clear_ui(frame)
                func(frame, filt)

            create_column_selector_screen(column_frame, cols, on_col)

    # TabView anlegen
    tabs = ctk.CTkTabview(container, width=900, height=600, command=_on_tab_changed)
    tabs.pack(fill="both", expand=True)
    for name in tab_map:
        tabs.add(name)

    # Erstes Tab
    first = next(iter(tab_map))
    tabs.set(first)
    _on_tab_changed()
