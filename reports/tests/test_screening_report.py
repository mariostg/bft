import pandas as pd
import pytest

from bft.management.commands import populate
from reports.utils import CostCenterScreeningReport


@pytest.mark.django_db
class TestCostCenterScreeningReport:

    def test_cost_element_allocation(self, populatedata, upload):
        r = CostCenterScreeningReport()
        expected_ce = {"2184A3", "8484WA", "8484YA"}
        data = r.cost_element_allocations("2184a3", "c113", 2023, 1)
        ce = set(pd.DataFrame(data).T["Cost Element"])
        assert 3 == len(data)
        assert expected_ce == ce

    def test_cost_element_allocation_non_existing_fund(self, populatedata, upload):
        r = CostCenterScreeningReport()
        data = r.cost_element_allocations("2184a3", "c999", 2023, 1)
        assert 0 == len(data)

    def test_cost_element_line_item_using_fund_center(self, populatedata, upload):
        r = CostCenterScreeningReport()
        data = r.cost_element_line_items("2184a3", "c113")
        assert 1 == len(data)
