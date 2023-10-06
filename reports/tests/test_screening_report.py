import pytest
from reports.utils import CostCenterScreeningReport
from costcenter.models import CostCenterAllocation, Fund, CostCenterManager, ForecastAdjustment
from bft.management.commands import populate, uploadcsv
import numpy as np
import pandas as pd


@pytest.mark.django_db
class TestCostCenterScreeningReport:
    def test_cost_center_screening_report_empty(self):
        r = CostCenterScreeningReport()
        assert True == r.cost_center_screening_report().empty

    def test_cost_center_screening_report(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

        assert 0 < len(CostCenterScreeningReport().cost_center_screening_report())

    # Financial Structure Tests
    def test_financial_structure_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

        data = CostCenterScreeningReport().financial_structure_dataframe()
        assert False == data.empty

    def test_financial_structure_dataframe_empty(self):
        r = CostCenterScreeningReport()
        data = r.financial_structure_dataframe()
        assert True == isinstance(data, pd.DataFrame)
        assert True == data.empty
