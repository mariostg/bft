import pytest
from costcenter.models import FundCenterManager, CostCenterManager
from reports.utils import CostCenterScreeningReport
from bft.management.commands import populate, uploadcsv
import pandas as pd


@pytest.mark.django_db
class TestCostCenterScreeningReport:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()
        self.expected_keys = (
            "Cost Element",
            "Cost Element Name",
            "Fund Center ID",
            "Parent ID",
            "Fund",
            "Path",
            "Parent Path",
            "Parent Fund Center",
            "Allocation",
            "Type",
        )

    @pytest.fixture
    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_cost_element_allocation(self, populate, upload):
        r = CostCenterScreeningReport()
        expected_ce = set(["2184A3", "8484WA", "8484YA"])
        data = r.cost_element_allocations("2184a3", "c113", 2023, 1)
        ce = set(pd.DataFrame(data).T["Cost Element"])
        assert 3 == len(data)
        assert expected_ce == ce

    def test_cost_element_allocation_non_existing_fund(self, populate, upload):
        r = CostCenterScreeningReport()
        data = r.cost_element_allocations("2184a3", "c999", 2023, 1)
        assert 0 == len(data)

    def test_cost_element_line_item_using_fund_center(self, populate, upload):
        r = CostCenterScreeningReport()
        data = r.cost_element_line_items("2184a3", "c113")
        assert 1 == len(data)
