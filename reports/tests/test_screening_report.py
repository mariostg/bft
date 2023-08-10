import pytest
from reports.utils import Report
from costcenter.models import CostCenterAllocation, Fund, CostCenterManager, ForecastAdjustment
from encumbrance.management.commands import populate, uploadcsv
import numpy as np


@pytest.mark.django_db
class TestReports:
    def test_cost_center_screening_report_empty(self):
        r = Report()
        assert True == r.cost_center_screening_report().empty

    def test_cost_center_screening_report(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

        r = Report()
        assert 0 < len(r.cost_center_screening_report())

    # Financial Structure Tests
    def test_financial_structure_data(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

        r = Report()
        data = r.financial_structure_data()
        assert False == data.empty

    def test_financial_structure_data_empty(self):
        r = Report()
        data = r.financial_structure_data()
        assert None == data
