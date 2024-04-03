import pandas as pd
import pytest

from bft.management.commands import populate, uploadcsv
from bft.models import (CostCenter, CostCenterAllocation, CostCenterManager,
                        ForecastAdjustment, Fund, FundCenter, Source)


@pytest.mark.django_db
class TestCostCenterManager:
    @pytest.fixture
    def setup(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        parent = FundCenter.objects.create(**fc)
        fund = {"fund": "C113"}
        fund = Fund.objects.create(**fund)
        source = Source.objects.create(**{"source": "Basement"})
        cc = {
            "costcenter": "8484ZZ",
            "shortname": "bedroom",
            "sequence": "1",
            "costcenter_parent": parent,
            "fund": fund,
            "source": source,
        }
        CostCenter.objects.create(**cc)

    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    @pytest.fixture
    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="test-data/encumbrance_2184A3.txt")

    # Cost Center Tests
    def test_a_given_cost_center_exists(self, setup):
        assert True == CostCenterManager().exists("8484ZZ")

    def test_a_given_cost_center_does_not_exists(self, setup):
        assert False == CostCenterManager().exists("9999aa")

    def test_no_cost_center_exists(self):
        assert False == CostCenterManager().exists()

    def test_cost_center_exists(self, setup):
        assert True == CostCenterManager().exists()

    def test_cost_center_dataframe_empty(self):
        r = CostCenterManager()
        assert 0 == len(r.cost_center_dataframe(pd.DataFrame))

    def test_cost_center_dataframe_no_data(self, populate):
        r = CostCenterManager()
        with pytest.raises(TypeError):
            r.cost_center_dataframe()

    def test_cost_center_dataframe(self, populate):
        CCM = CostCenterManager()
        cc = CCM.get_sibblings("2184A3")
        cc_df = CCM.cost_center_dataframe(cc)
        print(cc_df)
        assert "Costcenter_ID" in cc_df.columns
        assert "Cost Center" in cc_df.columns
        assert "Fund Center" in cc_df.columns
        assert "Cost Center Name" in cc_df.columns
        assert CostCenter.objects.all().count() == len(cc_df)

    def test_allocation_dataframe_empty(self):
        r = CostCenterManager()
        assert True == r.allocation_dataframe().empty

    def test_allocation_dataframe(self, populate):
        df = CostCenterManager().allocation_dataframe(costcenter="8484WA")
        assert 1 == len(df)
        assert "Allocation" in df.columns

    def test_allocation_dataframe_columns(self, populate):
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8484WA")
        alloc = CostCenterAllocation(fund=fund, costcenter=costcenter, amount=1000)
        alloc.save()
        columns = CostCenterManager().allocation_dataframe().columns
        for c in ["Fund Center", "Cost Center", "Fund", "Allocation", "FY"]:
            assert c in columns

    def test_get_sibblings_with_fundcenter_string(self, populate):
        CCM = CostCenterManager()
        siblings = CCM.get_sibblings("2184A3")
        print(siblings)

    # Forecast Adjustment Tests
    def test_forecast_adjustment_dataframe_empty(self):
        assert True == CostCenterManager().forecast_adjustment_dataframe().empty

    def test_forecast_adjustment_dataframe(self, populate, upload):
        fund = Fund.objects.all().first()
        costcenter = CostCenterManager().cost_center("8484WA")
        ForecastAdjustment(fund=fund, costcenter=costcenter, amount=1000).save()

        df = CostCenterManager().forecast_adjustment_dataframe()
        assert 1 == len(df)
        assert "Forecast Adjustment" in df.columns
