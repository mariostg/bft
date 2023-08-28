import pytest
from reports.utils import AllocationReport
from bft.management.commands import populate
from costcenter.models import (
    FundCenterAllocation,
    FundManager,
    FundCenterManager,
    CostCenterManager,
    CostCenterAllocation,
)
import pandas as pd


@pytest.mark.django_db
class TestUtilsAllocationReport:
    fcm = FundCenterManager()
    ccm = CostCenterManager()
    fca = FundCenterAllocation()
    cca = CostCenterAllocation()
    root_fundcenter = "1111AA"
    fund = "C113"
    fy = 2023
    quarter = "1"

    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()
        root_fc = self.fcm.fundcenter(self.root_fundcenter)
        cc = self.ccm.cost_center("8486C2")
        _fund = FundManager().fund(self.fund)

        FundCenterAllocation.objects.create(fundcenter=root_fc, amount=1000, fy=2023, quarter="1", fund=_fund)
        FundCenterAllocation.objects.create(
            fundcenter=self.fcm.fundcenter("1111AC"), amount=500, fy=2023, quarter="1", fund=_fund
        )
        CostCenterAllocation.objects.create(costcenter=cc, amount=250, fy=2023, quarter="1", fund=_fund)

    def test_we_have_fund_centers(self, setup):
        fc = self.fcm.fund_center_exist("2222BB")
        assert True == fc

        d = CostCenterAllocation.objects.all()
        assert len(d) > 0
        d = FundCenterAllocation.objects.all()
        assert len(d) > 0

    def test_family_list(self, setup):
        r = AllocationReport()
        r._get_family_list("1111AA")
        assert 3 == len(r.family_list)
        assert 2 == len(r.family_list[0])
        assert 4 == len(r.family_list[1])
        assert 1 == len(r.family_list[2])

    def test_family_dataframe(self, setup):
        r = AllocationReport()
        family_df = r.family_dataframe()
        assert 8 == len(family_df)

    def test_fc_allocation_dataframe(self, setup):
        r = AllocationReport()
        family_df = r.family_dataframe()
        fc_allocation_df = r.fc_allocation_dataframe(family_df, self.fund, self.fy, self.quarter)
        assert 2 == len(fc_allocation_df)

    def test_fc_allocation_dataframe_outside_quarter(self, setup):
        r = AllocationReport()
        family_df = r.family_dataframe()
        fc_allocation_df = r.fc_allocation_dataframe(family_df, self.fund, self.fy, "Q3")
        assert 0 == len(fc_allocation_df)

    def test_cc_allocation_dataframe(self, setup):
        r = AllocationReport()
        family_df = r.family_dataframe()
        cc_allocation_df = r.cc_allocation_dataframe(family_df, self.fund, self.fy, self.quarter)
        assert 1 == len(cc_allocation_df)

    def test_cc_allocation_dataframe_outside_quarter(self, setup):
        r = AllocationReport()
        family_df = r.family_dataframe()
        cc_allocation_df = r.cc_allocation_dataframe(family_df, self.fund, self.fy, "Q3")
        assert 0 == len(cc_allocation_df)

    def test_allocation_status_report(self, setup):

        r = AllocationReport()

        data = r.allocation_status_dataframe(self.root_fundcenter, self.fund, self.fy, self.quarter)
        assert pd.DataFrame == type(data)
        assert 3 == len(data)

    def test_allocation_status_report_outside_quarter(self, setup):

        r = AllocationReport()

        data = r.allocation_status_dataframe(self.root_fundcenter, self.fund, self.fy, "Q3")
        assert pd.DataFrame == type(data)
        assert 0 == len(data)
