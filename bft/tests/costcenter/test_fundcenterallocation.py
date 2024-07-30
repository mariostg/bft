import pytest
from django.db.models import Sum

from bft.models import (CostCenterAllocation, CostCenterManager, Fund,
                        FundCenterAllocation, FundCenterManager, FundManager)


@pytest.mark.django_db
class TestFundCenterAllocation:
    @pytest.fixture
    def setup(self):
        self.C113 = Fund.objects.get(fund="C113")

    def test_create_fund_center_allocation(self, populatedata, setup):
        fc = FundCenterManager().fundcenter("2184A1")
        a = FundCenterAllocation.objects.create(
            fundcenter=fc, amount=1000, fy=2023, quarter="1", fund=self.C113
        )
        assert a.fundcenter.fundcenter == "2184A1"
        assert a.amount == 1000

    def test_get_costcenter_subordinate_allocation(self, populatedata):
        FundCenterAllocation.objects.all().delete()
        CostCenterAllocation.objects.all().delete()
        fc = FundCenterManager().fundcenter("2184A3")
        fund = FundManager().fund("C113")
        fy = 2023
        quarter = 1

        cc = CostCenterManager().cost_center(costcenter="8484WA")
        CostCenterAllocation.objects.create(costcenter=cc, amount=1000, fy=fy, quarter=quarter, fund=fund)

        cc = CostCenterManager().cost_center(costcenter="8484XA")
        CostCenterAllocation.objects.create(costcenter=cc, amount=2000, fy=fy, quarter=quarter, fund=fund)

        sub_alloc = CostCenterManager().get_sub_alloc(fc, fund, fy, quarter)
        assert 2 == sub_alloc.count()

    def test_get_fundcenter_subordinate_allocation(self, populatedata, setup):
        da2184 = FundCenterManager().fundcenter(fundcenter="2184DA")
        fc_alloc = FundCenterAllocation.objects.get(
            fundcenter=da2184, fy=2023, quarter="1", fund=self.C113
        )

        sub_alloc = FundCenterManager().get_sub_alloc(fc_alloc)
        assert 40000.99 == float(sub_alloc.aggregate(Sum("amount"))["amount__sum"])


@pytest.mark.django_db
class TestFundCenterAllocationManager:

    # Fund Allocations
    def test_fund_allocation_when_fund_valid_and_allocation_exists(self, populatedata):
        allocation = FundCenterAllocation().objects.fund("c113")
        assert 3 == allocation.count()

    def test_fund_allocation_when_fund_valid_and_no_allocation(self, populatedata):
        allocation = FundCenterAllocation.objects.fund("C523")
        assert 0 == allocation.count()

    def test_fund_allocation_when_fund_invalid(self, populatedata):
        allocation = FundCenterAllocation.objects.fund("C999")
        assert allocation is None

    # Fund Center allocation
    def test_fundcenter_allocation_when_fundcenter_valid_and_allocation_exists(self, populatedata):
        allocation = FundCenterAllocation.objects.fundcenter("2184da")
        assert 1 == allocation.count()

    def test_fundcenter_allocation_when_fundcenter_valid_and_no_allocation(self, populatedata):
        allocation = FundCenterAllocation.objects.fundcenter("2184BE")
        assert 0 == allocation.count()

    def test_fundcenter_allocation_when_fundcenter_invalid(self, populatedata):
        allocation = FundCenterAllocation.objects.fundcenter("21ZZZ")
        assert allocation is None

    # FY
    def test_fy_allocation_when_allocation_exists(self, populatedata):
        allocation = FundCenterAllocation.objects.fy(2023)
        assert 3 == allocation.count()

    def test_fy_allocation_when_no_allocation(self, populatedata):
        allocation = FundCenterAllocation.objects.fy(3000)
        assert 0 == allocation.count()

    # Quarter
    def test_quarter_allocation_when_allocation_exists(self, populatedata):
        allocation = FundCenterAllocation.objects.quarter(1)
        assert 3 == allocation.count()

    def test_quarter_allocation_when_no_allocation(self, populatedata):
        allocation = FundCenterAllocation.objects.quarter(4)
        assert 0 == allocation.count()

    def test_quarter_allocation_when_quarter_invalid(self, populatedata):
        allocation = FundCenterAllocation.objects.quarter(6)
        assert allocation is None

    def test_descendants_fundcenter_allocation(self, populatedata):
        allocation = FundCenterAllocation.objects.descendants_fundcenter("2184DA")
        assert 3 == allocation.count()

    def test_descendants_costcenter_allocation(self, populatedata):
        allocation = CostCenterAllocation.objects.descendants_costcenter("2184DA")
        assert 2 == allocation.count()

    # Fund and Fund Center
    def test_fundcenter_and_fund_when_allocation_exists(self, populatedata):
        fc = "2184da"
        fund = None
        allocation = FundCenterAllocation.objects.fundcenter(fc).fund(fund)
        assert 1 == allocation.count()


@pytest.mark.django_db
class TestCostCenterAllocationManager:

    # Fund Allocations
    def test_fundcenter_allocation_when_fund_valid_and_allocation_exists(self, populatedata):
        fund_allocation = CostCenterAllocation.objects.fund("c113")
        assert 2 == fund_allocation.count()

    # Cost Center Allocations
    def test_costcenter_allocation_when_fund_valid_and_allocation_exists(self, populatedata):
        allocation = CostCenterAllocation.objects.costcenter("8484wa")
        assert 1 == allocation.count()
