from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QTableWidget, QTabWidget

from src.modules.component_inventory import CostAnalysisDialog


class _FakeDb:
    def __init__(self) -> None:
        self.inventory_items = [
            {
                "id": 3,
                "component_name": "Berger 140 Hybrid",
                "component_type": "bullet",
                "lot_number": "B-LOT-2",
                "quantity": 500,
                "unit": "pcs",
                "cost_per_unit": 0.62,
                "purchase_date": "2026-03-10",
                "created_date": "2026-03-10 12:00:00",
                "manufacturer": "Berger",
                "notes": "Latest lot",
            },
            {
                "id": 2,
                "component_name": "N150",
                "component_type": "powder",
                "lot_number": "P-LOT-2",
                "quantity": 1000,
                "unit": "gr",
                "cost_per_unit": 0.041,
                "purchase_date": "2026-03-08",
                "created_date": "2026-03-08 09:00:00",
                "manufacturer": "Vihtavuori",
                "notes": "",
            },
            {
                "id": 1,
                "component_name": "N150",
                "component_type": "powder",
                "lot_number": "P-LOT-1",
                "quantity": 1000,
                "unit": "gr",
                "cost_per_unit": 0.038,
                "purchase_date": "2026-02-01",
                "created_date": "2026-02-01 09:00:00",
                "manufacturer": "Vihtavuori",
                "notes": "",
            },
        ]
        self.loading_sessions = [
            {
                "date": "2026-03-20",
                "quantity": 50,
                "total_cost": 87.5,
                "powder_weight_min": 41.5,
                "powder_weight_max": 42.5,
            }
        ]

    def execute_query(self, query: str):
        if "FROM inventory_items" in query:
            return list(self.inventory_items)
        if "FROM loading_sessions" in query:
            return list(self.loading_sessions)
        raise AssertionError(f"Unexpected query: {query}")


@pytest.mark.core
def test_cost_analysis_dialog_uses_real_db_rows(monkeypatch):
    fake_db = _FakeDb()
    monkeypatch.setattr("src.modules.component_inventory.get_database", lambda: fake_db)

    dialog = CostAnalysisDialog()

    tabs = dialog.findChild(QTabWidget)
    assert tabs is not None

    cost_table = tabs.widget(0).findChild(QTableWidget)
    assert cost_table is not None
    assert cost_table.rowCount() >= 2
    assert cost_table.item(0, 1).text() == "Berger 140 Hybrid"
    assert cost_table.item(1, 1).text() == "N150"

    purchase_table = tabs.widget(2).findChild(QTableWidget)
    assert purchase_table is not None
    assert purchase_table.item(0, 1).text() == "Berger 140 Hybrid"

    trend_table = tabs.widget(3).findChild(QTableWidget)
    assert trend_table is not None
    assert trend_table.item(0, 1).text() == "N150"
    assert trend_table.item(0, 5).text().startswith("+0.003")

    dialog.close()
