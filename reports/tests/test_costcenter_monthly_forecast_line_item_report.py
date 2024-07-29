import pytest

from bft.management.commands import populate
from reports.utils import CostCenterMonthlyForecastLineItemReport


@pytest.mark.django_db
class TestCostCenterMonthlyForecastLineItemReport:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()

    def test_sum_line_items(self, setup, upload):
        report = CostCenterMonthlyForecastLineItemReport(fy=2023, period=1)
        results = report.sum_forecast_line_item()[0]
        assert 245000 == results["line_item_forecast"]
