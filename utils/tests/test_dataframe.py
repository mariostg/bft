import pytest
from utils.dataframe import BFTDataFrame
from bft.management.commands import populate, uploadcsv, monthlydata
from reports.models import CostCenterMonthly
from reports.utils import CostCenterMonthlyReport
from costcenter.models import CostCenter, Fund
from lineitems.models import LineItem
from django.db import models


@pytest.mark.django_db
class TestDataFrame:
    fy = 2023
    period = 1

    def test_cost_center_model_fields(self):
        d = BFTDataFrame(CostCenter)
        print(d.model_fields)
        assert 0 < len(d.model_fields)

    def test_dataframe_with_queryset(self):
        hnd = populate.Command()
        hnd.handle()

        d = BFTDataFrame(CostCenter)
        qst = CostCenter.objects.all()
        d.build(qst)

        assert len(qst) == len(d.dataframe)

    def test_dataframe_without_queryset(self):
        hnd = populate.Command()
        hnd.handle()

        d = BFTDataFrame(CostCenter)

        d.build()
        print(d.dataframe)
        assert 0 < len(d.dataframe)
        assert CostCenter.objects.all().count() == len(d.dataframe)

    def test_dataframe_fields_are_capitalized(self):
        hnd = populate.Command()
        hnd.handle()

        d = BFTDataFrame(CostCenter)
        for c in d.dataframe_fields:
            assert d.dataframe_fields[c][0] == d.dataframe_fields[c][0].upper()
