import pytest
from reports.utils import AllocationStatusReport
from bft.management.commands import populate
from costcenter.models import (
    FundCenterAllocation,
    FundManager,
    CostCenter,
    FundCenter,
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
    quarter = 1

    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()

    def test_we_have_fund_centers(self, setup):
        fc = self.fcm.fund_center_exist("2184AA")
        assert True == fc

    def test_we_have_fund_fc_allocation(self, setup):
        assert 2 == FundCenterAllocation.objects.count()

    def test_we_have_fund_cc_allocation(self, setup):
        assert 2 == CostCenterAllocation.objects.count()

    def test_family_dataframe(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe()
        assert FundCenter.objects.count() + CostCenter.objects.count() == len(family_df)

    def test_fc_allocation_dataframe(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe()
        fc_allocation_df = r.fc_allocation_dataframe(family_df, self.fund, self.fy, self.quarter)
        assert 2 == len(fc_allocation_df)

    def test_fc_allocation_dataframe_outside_quarter(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe()
        fc_allocation_df = r.fc_allocation_dataframe(family_df, self.fund, self.fy, 4)
        assert True == fc_allocation_df.empty

    def test_cc_allocation_dataframe(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe()
        cc_allocation_df = r.cc_allocation_dataframe(family_df, self.fund, self.fy, self.quarter)
        assert 2 == len(cc_allocation_df)

    def test_cc_allocation_dataframe_outside_quarter(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe()
        cc_allocation_df = r.cc_allocation_dataframe(family_df, self.fund, self.fy, 4)
        assert 0 == len(cc_allocation_df)

    def test_allocation_status_report(self, setup):

        r = AllocationStatusReport()
        data = r.allocation_status_dataframe(self.root_fundcenter, self.fund, self.fy, self.quarter)
        assert pd.DataFrame == type(data)
        assert 4 == len(data)

    def test_allocation_status_report_outside_quarter(self, setup):

        r = AllocationStatusReport()

        data = r.allocation_status_dataframe(self.root_fundcenter, self.fund, self.fy, 4)
        assert pd.DataFrame == type(data)
        assert 0 == len(data)
