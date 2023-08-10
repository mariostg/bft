import pytest
from costcenter.models import CostCenter, CostCenterManager, CostCenterAllocation, Fund, ForecastAdjustment
from encumbrance.management.commands import populate


@pytest.mark.django_db
class TestCostCenterManager:
    # Cost Center Tests
    def test_cost_center_dataframe_empty(self):
        r = CostCenterManager()
        assert 0 == len(r.cost_center_dataframe())

    def test_cost_center_dataframe_no_data(self):
        hnd = populate.Command()
        hnd.handle()

        r = CostCenterManager()
        assert 3 == len(r.cost_center_dataframe())

    def test_cost_center_dataframe(self):
        hnd = populate.Command()
        hnd.handle()

        CCM = CostCenterManager()
        cc = CCM.get_sibblings("1111AB")
        assert 2 == len(CCM.cost_center_dataframe(cc))

    def test_allocation_dataframe_empty(self):
        r = CostCenterManager()
        assert True == r.allocation_dataframe().empty

    def test_allocation_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8486b1")
        alloc = CostCenterAllocation(fund=fund, costcenter=costcenter, amount=1000)
        alloc.save()
        r = CostCenterManager()
        r.allocation_dataframe(costcenter=costcenter)
        assert 1 == len(r.allocation_dataframe(costcenter=costcenter))

    def test_allocation_dataframe_columns(self):
        hnd = populate.Command()
        hnd.handle()
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8486b1")
        alloc = CostCenterAllocation(fund=fund, costcenter=costcenter, amount=1000)
        alloc.save()
        columns = CostCenterManager().allocation_dataframe().columns
        for c in ["Fund Center", "Cost Center", "Fund", "Allocation", "FY"]:
            assert c in columns

    def test_get_sibblings_with_fundcenter_string(self):
        hnd = populate.Command()
        hnd.handle()
        CCM = CostCenterManager()
        siblings = CCM.get_sibblings("1111AB")
        print(siblings)

    # Forecast Adjustment Tests
    def test_forecast_adjustment_dataframe_empty(self):
        assert True == CostCenterManager().forecast_adjustment_dataframe().empty

    def test_forecast_adjustment_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8486b1")
        ForecastAdjustment(fund=fund, costcenter=costcenter, amount=1000).save()

        assert 1 == len(CostCenterManager().forecast_adjustment_dataframe())
