import pytest
from costcenter.models import CostCenter, CostCenterManager, CostCenterAllocation, Fund, ForecastAdjustment
from bft.management.commands import populate
import pandas as pd


@pytest.mark.django_db
class TestCostCenterManager:
    # Cost Center Tests
    def test_cost_center_allocation_at_quarter_0(self):
        hnd = populate.Command()
        hnd.handle()

        CCM = CostCenterManager()
        a = CCM.allocation("8486B1", "C113", 2023, 0)
        assert 0 == len(a)

    def test_cost_center_allocation_at_quarter_1(self):
        hnd = populate.Command()
        hnd.handle()

        CCM = CostCenterManager()
        a = CCM.allocation("8486B1", "C113", 2023, 1)
        assert 1 == len(a)

    def test_cost_center_dataframe_empty(self):
        r = CostCenterManager()
        assert 0 == len(r.cost_center_dataframe(pd.DataFrame))

    def test_cost_center_dataframe_no_data(self):
        hnd = populate.Command()
        hnd.handle()

        r = CostCenterManager()
        with pytest.raises(TypeError):
            r.cost_center_dataframe()

    def test_cost_center_dataframe(self):
        hnd = populate.Command()
        hnd.handle()

        CCM = CostCenterManager()
        cc = CCM.get_sibblings("1111AB")
        assert 2 == len(CCM.cost_center_dataframe(cc))

    def test_cost_center_dataframe_column_id(self):
        hnd = populate.Command()
        hnd.handle()

        df = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())
        assert True == ("Cost Center ID" in df.columns)

    def test_allocation_dataframe_empty(self):
        r = CostCenterManager()
        assert True == r.allocation_dataframe().empty

    def test_allocation_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        r = CostCenterManager()
        assert 1 == len(r.allocation_dataframe(costcenter="8486B1"))

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
