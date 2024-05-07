import pytest
from bft.management.commands import populate, uploadcsv

from reports.utils import CostCenterMonthlyForecastLineItemReport
from bft.models import LineForecast, LineItem


@pytest.mark.django_db
class TestCostCenterMonthlyForecastLineItemReport:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="test-data/encumbrance_2184A3.txt")

    def test_sum_line_items(self, setup):
        report = CostCenterMonthlyForecastLineItemReport(fy=2023, period=1)
        results = report.sum_forecast_line_item()[0]
        print(results)
        assert 245000 == results["line_item_forecast"]
