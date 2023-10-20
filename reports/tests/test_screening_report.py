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

    def test_fund_center_alloc_to_dict_with_one_item(self, populate, upload):
        r = CostCenterScreeningReport()

        alloc = FundCenterManager().allocation(fundcenter="2184a3", fund="c113", fy=2023, quarter=1)
        data = r.fund_center_alloc_to_dict(alloc)

        assert 1 == len(data)
        _keys = data.values()
        assert set(list(data[list(data.keys())[0]].keys())) == set(self.expected_keys)

    def test_fund_center_alloc_to_dict_with_many_item(self, populate, upload):
        r = CostCenterScreeningReport()

        alloc = FundCenterManager().allocation(fundcenter=["2184da", "2184a3"], fund="c113", fy=2023, quarter=1)
        data = r.fund_center_alloc_to_dict(alloc)

        assert 2 == len(data)
        assert set(list(data[list(data.keys())[0]].keys())) == set(self.expected_keys)

    def test_cost_center_alloc_to_dict_with_many_item(self, populate, upload):
        r = CostCenterScreeningReport()

        alloc = CostCenterManager().allocation(costcenter=["8484wa", "8484xa"], fund="c113", fy=2023, quarter=1)
        data = r.cost_center_alloc_to_dict(alloc)

        assert 2 == len(data)
        assert set(list(data[list(data.keys())[0]].keys())) == set(self.expected_keys)

    def test_cost_element_allocation(self, populate, upload):
        r = CostCenterScreeningReport()
        expected_ce = set(["2184A3", "8484WA", "8484XA"])
        data = r.cost_element_allocations("2184a3")
        ce = set(pd.DataFrame(data).T["Cost Element"])
        assert 3 == len(data)
        assert expected_ce == ce

    def test_cost_element_line_item_using_fund_center(self, populate, upload):
        r = CostCenterScreeningReport()
        data = r.cost_element_line_items("2184a3", "c113")
        assert 1 == len(data)
