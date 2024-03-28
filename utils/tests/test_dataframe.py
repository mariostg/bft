import pytest
from utils.dataframe import BFTDataFrame
from bft.exceptions import BFTDataFrameExceptionError
from bft.management.commands import populate, uploadcsv, monthlydata
from reports.models import CostCenterMonthly
from reports.utils import CostCenterMonthlyReport
from bft.models import CostCenter, FundCenter, Fund, LineItem
from django.db import models
import pandas as pd


@pytest.mark.django_db
class TestDataFrame:
    fy = 2023
    period = 1

    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()

    @pytest.fixture
    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_dataframe_without_params(self):
        with pytest.raises(TypeError):
            df = BFTDataFrame()

    def test_cost_center_model_fields(self):
        d = BFTDataFrame(CostCenter)
        assert 0 < len(d.dataframe_fields)

    def test_dataframe_with_unhandled_datatype(self, setup):
        df = BFTDataFrame(Fund)
        with pytest.raises(BFTDataFrameExceptionError):
            df.build("Some invalid data type")

    def test_dataframe_with_dictionary(self, setup):
        fund_dict = {"id": 9, "fund": "C113", "name": "National Procurement", "vote": "1", "download": True}
        df = BFTDataFrame(Fund)
        df_fund = df.build(fund_dict)
        print(df_fund.Fund)
        assert True == isinstance(df_fund, pd.DataFrame)
        # Confirm columns have been renamed
        assert "C113" == df_fund.at[0, "Fund"]
        assert "National Procurement" == df_fund.at[0, "Name"]
        assert 9 == df_fund.at[0, "Fund_ID"]

    def test_dataframe_with_model_instance(self, setup):
        fund = Fund.objects.get(fund="C113")
        df = BFTDataFrame(Fund)
        df_fund = df.build(fund)
        assert True == isinstance(df_fund, pd.DataFrame)
        # Confirm columns have been renamed
        assert "C113" == df_fund.at[0, "Fund"]
        assert "Basement Procurement" == df_fund.at[0, "Name"]
        assert fund.id == df_fund.at[0, "Fund_ID"]

    def test_dataframe_with_queryset(self, setup):
        d = BFTDataFrame(CostCenter)
        qst = CostCenter.objects.all()
        d.build(qst)

        assert len(qst) == len(d.dataframe)

    def test_dataframe_fields_are_capitalized(self, setup):
        # Testing with 3 models, that should be more than enough.
        d = BFTDataFrame(CostCenter)
        for c in d.dataframe_fields:
            assert d.dataframe_fields[c][0] == d.dataframe_fields[c][0].upper()

        d = BFTDataFrame(FundCenter)
        for c in d.dataframe_fields:
            assert d.dataframe_fields[c][0] == d.dataframe_fields[c][0].upper()

        d = BFTDataFrame(LineItem)
        for c in d.dataframe_fields:
            assert d.dataframe_fields[c][0] == d.dataframe_fields[c][0].upper()
