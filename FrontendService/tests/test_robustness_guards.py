from datetime import date, datetime

from src.controllers.AccountController import AccountController
from src.data.DataManager import DataManager


class DummyDataManager:
    def __init__(self):
        self.add_calls = []
        self.calculate_calls = []

    def duplicate_account(self, *_args, **_kwargs):
        return False

    def create_account(self, person_id, account_type, account_data):
        self.add_calls.append((person_id, account_type, account_data))
        return True

    def get_person(self, _person_id):
        return {"id": "p1", "Konten": []}

    def update_depot_details(self, *_args, **_kwargs):
        self.calculate_calls.append("depot")

    def calculate_festgeld_for_date(self, *_args, **_kwargs):
        return 0.0

    def update_account_balance(self, *_args, **_kwargs):
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
        {"Kontotyp": "Depot", "Data": None},
        {"Kontotyp": "Depot", "Data": {"Bank": "X", "Deponummer": "1"}},
        None,
        {"Data": {"Bank": "Y"}},
    ]

    controller.update_account_overview({"id": "p1"}, datetime(2026, 1, 1), entries)

    assert len(controller.data_manager.add_calls) == 1
    assert controller.data_manager.add_calls[0][1] == "Depot"


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
            "konto": {"Kontotyp": "Depot", "Bank": "X", "Deponummer": "D1", "DepotDetails": []},
            "details": [{"ISIN": "DE000A1EWWW0", "Menge": 1.0}],
        },
        {
            "konto": {"Kontotyp": "Girokonto", "Bank": "Y", "Kontonummer": "K1"},
            "balance": 123.45,
        },
    ]

    controller.update_account_overview({"id": "p1"}, datetime(2026, 1, 1), entries)

    assert len(controller.data_manager.add_calls) == 2
    assert controller.data_manager.add_calls[0][2]["DepotDetails"] == [{"ISIN": "DE000A1EWWW0", "Menge": 1.0}]
    assert controller.data_manager.add_calls[1][2]["Kontostand"] == 123.45
