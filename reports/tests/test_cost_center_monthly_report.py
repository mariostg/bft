import pytest

from reports.utils import CostCenterMonthlyEncumbranceReport


@pytest.mark.django_db
class TestCostCenterMonthlyReport:

    def test_period_out_of_range(self):
        cm = CostCenterMonthlyEncumbranceReport(2023, 19, "8484WA", "C113")
        assert cm.period is None

    def test_sum_line_items(self, populatedata, upload):
        cm = CostCenterMonthlyEncumbranceReport(2023, 1, "8484WA", "C113")
        lines = cm.sum_line_items()
        assert 2 == len(lines)

    def test_line_item_columns(self, populatedata, upload):
        cm = CostCenterMonthlyEncumbranceReport(2023, 1, "8484WA", "C113")
        lines = cm.sum_line_items()
        assert {
            "costcenter",
            "fund",
            "spent",
            "commitment",
            "pre_commitment",
            "fund_reservation",
            "balance",
            "working_plan",
            "fy",
            "period",
        } == lines[0].keys()

    def test_insert_line_items(self, populatedata, upload):
        cm = CostCenterMonthlyEncumbranceReport(2023, 1, "8484WA", "C113")
        lines = cm.sum_line_items()
        inserted = cm.insert_line_items(lines)
        assert 2 == inserted

    def test_insert_line_items_when_none(self, populatedata):
        cm = CostCenterMonthlyEncumbranceReport(2023, 1, "8484WA", "C113")
        lines = []
        inserted = cm.insert_line_items(lines)
        assert 0 == inserted

    def test_dataframe_model_empty(self):
        r = CostCenterMonthlyEncumbranceReport(fy=2023, period=1, costcenter="8484WA", fund="C113")
        df = r.dataframe()

        assert True == df.empty
