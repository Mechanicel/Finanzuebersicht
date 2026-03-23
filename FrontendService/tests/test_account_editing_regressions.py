from datetime import date

from src.helpers.account_editing import (
    get_latest_balance_entry,
    recalculate_depot_after_account_edit,
    update_latest_balance_entry,
)


def test_get_latest_balance_entry_and_update_latest_balance_entry_keep_history_ordered():
    account = {
        "id": "g1",
        "Kontostaende": [
            "2026-01-05: 100.00",
            "2026-02-10: 150.00",
        ],
    }

    latest_date, latest_value = get_latest_balance_entry(account)
    assert latest_date == "2026-02-10"
    assert latest_value == 150.0

    update_latest_balance_entry(account, 175.0, date(2026, 3, 1))

    assert account["Kontostaende"] == [
        "2026-01-05: 100.00",
        "2026-02-10: 175.00",
    ]


def test_update_latest_balance_entry_creates_new_entry_when_history_missing():
    account = {"id": "g2", "Kontostaende": []}

    update_latest_balance_entry(account, 44.5, date(2026, 1, 7))

    assert account["Kontostaende"] == ["2026-01-07: 44.50"]


def test_recalculate_depot_after_account_edit_returns_true_for_successful_call():
    class Controller:
        def __init__(self):
            self.calls = []

        def calculate_depot(self, person, selected_date):
            self.calls.append((person["id"], selected_date))

    controller = Controller()

    result = recalculate_depot_after_account_edit(controller, {"id": "p1"}, date(2026, 2, 1))

    assert result is True
    assert controller.calls == [("p1", date(2026, 2, 1))]


def test_recalculate_depot_after_account_edit_returns_false_on_error():
    class Controller:
        def calculate_depot(self, _person, _selected_date):
            raise RuntimeError("boom")

    result = recalculate_depot_after_account_edit(Controller(), {"id": "p1"}, date(2026, 2, 1))

    assert result is False
