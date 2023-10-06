import pytest
from bft.management.commands import populate, uploadcsv
from reports.utils import CostCenterMonthlyReport


@pytest.mark.django_db
class TestCostCenterMonthlyReport:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_period_out_of_range(self):
        with pytest.raises(
            ValueError,
            match="19 is not a valid period.  Expected value is one of 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14",
        ):
            CostCenterMonthlyReport(2023, 19)

    def test_sum_line_items(self, setup):
        cm = CostCenterMonthlyReport(2023, 1)
        lines = cm.sum_line_items()
        assert 2 == len(lines)

    def test_line_item_columns(self, setup):
        cm = CostCenterMonthlyReport(2023, 1)
        lines = cm.sum_line_items()
        assert set(
            [
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
                "source",
            ]
        ) == set(list(lines[0].keys()))

    def test_insert_line_items(self, setup):
        cm = CostCenterMonthlyReport(2023, 1)
        lines = cm.sum_line_items()
        inserted = cm.insert_line_items(lines)
        assert 2 == inserted

    def test_insert_line_items_when_none(self, setup):
        cm = CostCenterMonthlyReport(2023, 1)
        lines = []
        inserted = cm.insert_line_items(lines)
        assert 0 == inserted

    def test_dataframe_model_empty(self):
        r = CostCenterMonthlyReport(fy=2023, period=1)
        df = r.dataframe()

        assert True == df.empty
