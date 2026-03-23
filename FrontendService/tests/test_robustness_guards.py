from datetime import date, datetime

from src.controllers.AccountController import AccountController
from src.data.DataManager import DataManager


class DummyDataManager:
    def __init__(self):
        self.balance_calls = []
        self.depot_calls = []
        self.calculate_calls = []

    def get_person(self, _person_id):
        return {"id": "p1", "Konten": []}

    def update_depot_details(self, person_id, konto_id, details):
        self.depot_calls.append((person_id, konto_id, details))
        return True

    def update_account_balance(self, konto_id, date_str, value):
        self.balance_calls.append((konto_id, date_str, value))
        return True

    def calculate_depot(self, *_args, **_kwargs):
        self.calculate_calls.append("depot")

    def calculate_festgeld(self, *_args, **_kwargs):
        self.calculate_calls.append("festgeld")



def _make_data_manager_without_init():
    dm = DataManager.__new__(DataManager)
    dm._available = True
    dm.repository = None
    dm.settings = None
    dm._with_db_or_default = lambda fn, default: fn()
    return dm


def test_update_account_overview_skips_invalid_entries_and_none_data():
    controller = AccountController.__new__(AccountController)
    controller.data_manager = DummyDataManager()

    entries = [
        {"konto": {"id": "d1", "Kontotyp": "Depot"}, "details": [{"ISIN": "AAA", "Menge": 1}]},
        None,
        {"konto": {"Kontotyp": "Girokonto"}, "balance": 123.0},
    ]

    controller.update_account_overview({"id": "p1"}, datetime(2026, 1, 1), entries)

    assert controller.data_manager.depot_calls == [("p1", "d1", [{"ISIN": "AAA", "Menge": 1}])]
    assert controller.data_manager.balance_calls == []


def test_create_account_returns_false_for_none_account_data():
    dm = _make_data_manager_without_init()
    dm.get_person = lambda person_id: {"id": person_id, "Konten": []}

    result = dm.create_account("p1", "Depot", None)

    assert result is False


def test_get_person_data_returns_none_for_invalid_selected_person_type():
    dm = _make_data_manager_without_init()

    assert dm.get_person_data(None) is None
    assert dm.get_person_data("p1") is None


def test_duplicate_account_returns_false_for_invalid_account_data_type():
    dm = _make_data_manager_without_init()
    dm.get_person = lambda _person_id: {"id": "p1", "Konten": []}

    assert dm.duplicate_account("p1", "Girokonto", None) is False


def test_update_account_balance_skips_persons_without_id():
    dm = _make_data_manager_without_init()
    dm.load_personen = lambda: [{"Konten": [{"id": "k1", "Kontostaende": []}]}]

    assert dm.update_account_balance("k1", "2026-01-01", 1.0) is False


def test_calculate_depot_accepts_date_and_datetime_without_attribute_error():
    class DepotDummyDataManager:
        def __init__(self):
            self.price_dates = []

        def get_person(self, _person_id):
            return {
                "id": "p1",
                "Konten": [
                    {
                        "id": "d1",
                        "Kontotyp": "Depot",
                        "DepotDetails": [{"ISIN": "DE000A1EWWW0", "Menge": 2}],
                    }
                ],
            }

        def get_price(self, _isin, on_date):
            self.price_dates.append(on_date)
            return 10.0

        def get_company_name(self, _isin):
            return "Test AG"

        def update_depot_details(self, *_args, **_kwargs):
            return True

        def update_account_balance(self, *_args, **_kwargs):
            return True

    controller = AccountController.__new__(AccountController)
    controller.data_manager = DepotDummyDataManager()

    controller.calculate_depot({"id": "p1"}, date(2026, 1, 1))
    controller.calculate_depot({"id": "p1"}, datetime(2026, 1, 2, 12, 30))

    assert controller.data_manager.price_dates == [date(2026, 1, 1), date(2026, 1, 2)]


def test_update_account_overview_accepts_accountoverview_entry_shape():
    controller = AccountController.__new__(AccountController)
    controller.data_manager = DummyDataManager()

    entries = [
        {
            "konto": {"id": "d1", "Kontotyp": "Depot", "Bank": "X", "Deponummer": "D1", "DepotDetails": []},
            "details": [{"ISIN": "DE000A1EWWW0", "Menge": 1.0}],
        },
        {
            "konto": {"id": "g1", "Kontotyp": "Girokonto", "Bank": "Y", "Kontonummer": "K1"},
            "balance": 123.45,
        },
    ]

    controller.update_account_overview({"id": "p1"}, datetime(2026, 1, 1), entries)

    assert controller.data_manager.depot_calls == [("p1", "d1", [{"ISIN": "DE000A1EWWW0", "Menge": 1.0}])]
    assert controller.data_manager.balance_calls == [("g1", "2026-01-01", 123.45)]
