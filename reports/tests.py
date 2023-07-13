import pytest
from reports.utils import Report
from costcenter.models import CostCenterAllocation, Fund, CostCenterManager, ForecastAdjustment
from encumbrance.management.commands import populate, uploadcsv


@pytest.mark.django_db
class TestReports:
    def test_line_item_dataframe_no_line_items(self):
        r = Report()
        assert True == r.line_item_dataframe().empty

    def test_line_item_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        r = Report()

        li = r.line_item_dataframe()

        assert 7 == len(li)

    def test_line_forecast_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        from lineitems.models import LineForecast, LineItem

        li = LineItem.objects.all().first()
        data = {"forecastamount": 1000, "lineitem": li}
        fcst = LineForecast(**data)
        fcst.save()

        r = Report()
        li = r.forecast_dataframe()
        assert 1 == len(li)

    def test_fund_center_dataframe_empty(self):
        r = Report()
        assert 0 == len(r.fund_center_dataframe())

    def test_fund_center_dataframe(self):
        hnd = populate.Command()
        hnd.handle()

        r = Report()
        assert 5 == len(r.fund_center_dataframe())

    def test_cost_center_dataframe_empty(self):
        r = Report()
        assert 0 == len(r.cost_center_dataframe())

    def test_cost_center_dataframe(self):
        hnd = populate.Command()
        hnd.handle()

        r = Report()
        assert 3 == len(r.cost_center_dataframe())

    def test_line_item_detailed_empty(self):
        r = Report()
        assert True == r.line_item_detailed().empty

    def test_line_item_detailed(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

        r = Report()
        assert 7 == len(r.line_item_detailed())

    def test_cost_center_allocation_dataframe_empty(self):
        r = Report()
        assert True == r.cost_center_allocation_dataframe().empty

    def test_cost_center_allocation_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8486b1")
        alloc = CostCenterAllocation(fund=fund, costcenter=costcenter, amount=1000)
        alloc.save()
        r = Report()
        assert 1 == len(r.cost_center_allocation_dataframe())

    def test_cost_center_allocation_dataframe_columns(self):
        hnd = populate.Command()
        hnd.handle()
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8486b1")
        alloc = CostCenterAllocation(fund=fund, costcenter=costcenter, amount=1000)
        alloc.save()
        columns = Report().cost_center_allocation_dataframe().columns
        for c in ["Fund Center", "Cost Center", "Fund", "Allocation", "FY"]:
            assert c in columns

    def test_forecast_adjustment_dataframe_empty(self):
        r = Report()
        assert True == r.forecast_adjustment_dataframe().empty

    def test_forecast_adjustment_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8486b1")
        ForecastAdjustment(fund=fund, costcenter=costcenter, amount=1000).save()
        r = Report()

        assert 1 == len(r.forecast_adjustment_dataframe())

    def test_cost_center_screening_report_empty(self):
        r = Report()
        assert True == r.cost_center_screening_report().empty

    def test_cost_center_screening_report(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

        r = Report()
        print(r.cost_center_screening_report())
