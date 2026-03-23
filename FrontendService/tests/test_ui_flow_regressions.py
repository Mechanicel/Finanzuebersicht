from pathlib import Path
from datetime import date

from src.controllers.AccountController import AccountController
from src.helpers.ui_flow import filter_bank_names, extract_latest_balance


def test_refactored_screens_do_not_define_redundant_secondary_back_buttons():
    repo_root = Path(__file__).resolve().parents[1]
    screen_files = [
        "src/screens/PersonSelection.py",
        "src/screens/NewPerson.py",
        "src/screens/NewBank.py",
        "src/screens/BankAssignment.py",
        "src/screens/FreibetragInput.py",
        "src/screens/AccountAddition.py",
    ]

    for rel_path in screen_files:
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        assert "back_command=" in source
        assert 'secondary_button(bar, "Zurück"' not in source


def test_bank_assignment_filter_matches_substrings_case_insensitive():
    banks = ["Commerzbank", "Deutsche Bank", "ING", "N26"]

    assert filter_bank_names(banks, "") == banks
    assert filter_bank_names(banks, "bank") == ["Commerzbank", "Deutsche Bank"]
    assert filter_bank_names(banks, "ING") == ["ING"]
    assert filter_bank_names(banks, "foo") == []


def test_form_screens_use_grid_compatible_action_bar():
    repo_root = Path(__file__).resolve().parents[1]
    form_screens = [
        "src/screens/NewPerson.py",
        "src/screens/NewBank.py",
        "src/screens/FreibetragInput.py",
        "src/screens/AccountAddition.py",
        "src/screens/AccountEditing.py",
    ]

    for rel_path in form_screens:
        source = (repo_root / rel_path).read_text(encoding="utf-8")
        assert "action_bar_grid(" in source
        assert " action_bar(" not in source


def test_components_expose_separate_pack_and_grid_action_bar_helpers():
    components = (Path(__file__).resolve().parents[1] / "src/ui/components.py").read_text(encoding="utf-8")
    assert "def action_bar(parent):" in components
    assert "bar.pack(" in components
    assert "def action_bar_grid(" in components
    assert "bar.grid(" in components


def test_calculate_depot_updates_details_and_balance_for_pie_chart_source():
    class DepotValueDataManager:
        def __init__(self):
            self.updated_details = []
            self.updated_balances = []

        def get_person(self, _person_id):
            return {
                "id": "p1",
                "Konten": [
                    {
                        "id": "d1",
                        "Kontotyp": "Depot",
                        "DepotDetails": [
                            {"ISIN": "AAA", "Menge": 2},
                            {"ISIN": "BBB", "Menge": 3},
                        ],
                    }
                ],
            }

        def get_price(self, isin, _date):
            return {"AAA": 10.0, "BBB": 20.0}[isin]

        def get_company_name(self, isin):
            return isin

        def update_depot_details(self, person_id, konto_id, details):
            self.updated_details.append((person_id, konto_id, details))
            return True

        def update_account_balance(self, konto_id, datum_str, wert):
            self.updated_balances.append((konto_id, datum_str, wert))
            return True

    controller = AccountController.__new__(AccountController)
    dm = DepotValueDataManager()
    controller.data_manager = dm

    controller.calculate_depot({"id": "p1"}, date(2026, 1, 5))

    assert len(dm.updated_details) == 1
    assert len(dm.updated_balances) == 1
    konto_id, _datum, total = dm.updated_balances[0]
    assert konto_id == "d1"
    assert total == 80.0


def test_extract_latest_balance_supports_kontostaende_and_depotdetails_fallback():
    konto_with_balance = {"Kontotyp": "Depot", "Kontostaende": ["2026-01-05: 120.50"]}
    konto_with_details_only = {
        "Kontotyp": "Depot",
        "DepotDetails": [{"value": 50.0}, {"value": 70.0}],
    }

    assert extract_latest_balance(konto_with_balance) == 120.5
    assert extract_latest_balance(konto_with_details_only) == 120.0
