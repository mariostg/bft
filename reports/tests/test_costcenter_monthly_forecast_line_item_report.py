import pytest

from reports.utils import CostCenterMonthlyForecastLineItemReport


@pytest.mark.django_db
class TestCostCenterMonthlyForecastLineItemReport:

    def test_sum_line_items(self, populatedata, upload):
        report = CostCenterMonthlyForecastLineItemReport(fy=2023, period=1)
        results = report.sum_forecast_line_item()[0]
        assert 245000 == results["line_item_forecast"]
