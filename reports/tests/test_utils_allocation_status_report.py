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
    root_fundcenter = "2184da"
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

    def test_family_dataframe_valid_fund_center(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe("2184A3")
        assert 4 == len(family_df)

    def test_family_dataframe_invalid_fund_center(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe("2023")
        assert 0 == len(family_df)

    def test_fc_allocation_dataframe(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe("2184da")
        fc_allocation_df = r.fc_allocation_dataframe(family_df, self.fund, self.fy, self.quarter)
        assert 2 == len(fc_allocation_df)

    def test_fc_allocation_status_dataframe_when_no_costcenter_allocation(self, setup):
        CostCenterAllocation.objects.all().delete()
        r = AllocationStatusReport()
        fc_allocation_df = r.allocation_status_dataframe("2184DA", "C113", 2023, 1)
        assert 2 == len(fc_allocation_df)

    def test_fc_allocation_dataframe_outside_quarter(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe("2184da")
        fc_allocation_df = r.fc_allocation_dataframe(family_df, self.fund, self.fy, 4)
        assert 0 == sum(fc_allocation_df["Amount"])

    def test_cc_allocation_dataframe(self, setup):
        # CostCenterAllocation.objects.all().delete()
        r = AllocationStatusReport()
        family_df = r.family_dataframe("2184da")
        cc_allocation_df = r.cc_allocation_dataframe(family_df, self.fund, self.fy, self.quarter)
        assert 2 == len(cc_allocation_df)

    def test_cc_allocation_dataframe_outside_quarter(self, setup):
        r = AllocationStatusReport()
        family_df = r.family_dataframe("2184da")
        cc_allocation_df = r.cc_allocation_dataframe(family_df, self.fund, self.fy, 4)
        assert 0 == sum(cc_allocation_df["Amount"])

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
