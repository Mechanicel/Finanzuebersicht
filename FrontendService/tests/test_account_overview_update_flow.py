from datetime import date

from src.controllers.AccountController import AccountController


def test_update_account_overview_updates_existing_accounts_instead_of_creating_new_ones():
    class DataManagerStub:
        def __init__(self):
            self.balance_updates = []
            self.depot_updates = []
            self.create_calls = []

        def update_account_balance(self, konto_id, date_str, value):
            self.balance_updates.append((konto_id, date_str, value))
            return True

        def update_depot_details(self, person_id, konto_id, details):
            self.depot_updates.append((person_id, konto_id, details))
            return True

        def create_account(self, *args, **kwargs):
            self.create_calls.append((args, kwargs))
            return True

    controller = AccountController.__new__(AccountController)
    dm = DataManagerStub()
    controller.data_manager = dm

    entries = [
        {"konto": {"id": "g1", "Kontotyp": "Girokonto"}, "balance": 321.0},
        {"konto": {"id": "d1", "Kontotyp": "Depot"}, "details": [{"ISIN": "AAA", "Menge": 2.0}]},
    ]

    controller.update_account_overview({"id": "p1"}, date(2026, 1, 15), entries)

    assert dm.balance_updates == [("g1", "2026-01-15", 321.0)]
    assert dm.depot_updates == [("p1", "d1", [{"ISIN": "AAA", "Menge": 2.0}])]
    assert dm.create_calls == []


def test_update_account_overview_saves_non_depot_balance_for_selected_date():
    class DataManagerStub:
        def __init__(self):
            self.balance_updates = []

        def update_account_balance(self, konto_id, date_str, value):
            self.balance_updates.append((konto_id, date_str, value))
            return True

        def update_depot_details(self, *_args, **_kwargs):
            return True

    controller = AccountController.__new__(AccountController)
    dm = DataManagerStub()
    controller.data_manager = dm

    controller.update_account_overview(
        {"id": "p1"},
        date(2026, 2, 20),
        [{"konto": {"id": "g2", "Kontotyp": "Tagesgeld"}, "balance": 987.65}],
    )

    assert dm.balance_updates == [("g2", "2026-02-20", 987.65)]


def test_update_account_overview_saves_depot_details_for_existing_depot():
    class DataManagerStub:
        def __init__(self):
            self.depot_updates = []

        def update_account_balance(self, *_args, **_kwargs):
            return True

        def update_depot_details(self, person_id, konto_id, details):
            self.depot_updates.append((person_id, konto_id, details))
            return True

    controller = AccountController.__new__(AccountController)
    dm = DataManagerStub()
    controller.data_manager = dm

    details = [{"ISIN": "DE000A1EWWW0", "Menge": 4.0}]
    controller.update_account_overview(
        {"id": "p2"},
        date(2026, 2, 20),
        [{"konto": {"id": "d9", "Kontotyp": "Depot"}, "details": details}],
    )

    assert dm.depot_updates == [("p2", "d9", details)]
