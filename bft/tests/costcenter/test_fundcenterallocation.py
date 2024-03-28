import pytest
from bft.models import (
    CostCenterAllocation,
    FundCenterManager,
    FundCenterAllocation,
    Fund,
    CostCenterManager,
    FundManager,
)
from bft.management.commands import populate, uploadcsv
from django.db.models import Sum


@pytest.mark.django_db
class TestFundCenterAllocation:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()
        self.C113 = Fund.objects.get(fund="C113")

    def test_create_fund_center_allocation(self, populate):
        fc = FundCenterManager().fundcenter("2184A1")
        a = FundCenterAllocation.objects.create(
            fundcenter=fc, amount=1000, fy=2023, quarter="1", fund=self.C113
        )
        assert a.fundcenter.fundcenter == "2184A1"
        assert a.amount == 1000

    def test_get_costcenter_subordinate_allocation(self, populate):
        FundCenterAllocation.objects.all().delete()
        CostCenterAllocation.objects.all().delete()
        fc = FundCenterManager().fundcenter("2184A3")
        fund = FundManager().fund("C113")
        fy = 2023
        quarter = 1

        cc = CostCenterManager().cost_center(costcenter="8484WA")
        CostCenterAllocation.objects.create(
            costcenter=cc, amount=1000, fy=fy, quarter=quarter, fund=self.C113
        )

        cc = CostCenterManager().cost_center(costcenter="8484XA")
        CostCenterAllocation.objects.create(
            costcenter=cc, amount=2000, fy=fy, quarter=quarter, fund=self.C113
        )

        sub_alloc = CostCenterManager().get_sub_alloc(fc, fund, fy, quarter)
        assert 2 == sub_alloc.count()

    def test_get_fundcenter_subordinate_allocation(self, populate):
        da2184 = FundCenterManager().fundcenter(fundcenter="2184DA")
        fc_alloc = FundCenterAllocation.objects.get(
            fundcenter=da2184, fy=2023, quarter="1", fund=self.C113
        )

        sub_alloc = FundCenterManager().get_sub_alloc(fc_alloc)
        assert 40000.99 == float(sub_alloc.aggregate(Sum("amount"))["amount__sum"])


@pytest.mark.django_db
class TestFundCenterAllocationManager:
    @pytest.fixture
    def populate(self):
        self.FCA = FundCenterAllocation
        self.CCA = CostCenterAllocation
        hnd = populate.Command()
        hnd.handle()

    @pytest.fixture
    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    # Fund Allocations
    def test_fund_allocation_when_fund_valid_and_allocation_exists(self, populate):
        allocation = self.FCA.objects.fund("c113")
        assert 3 == allocation.count()

    def test_fund_allocation_when_fund_valid_and_no_allocation(self, populate):
        allocation = self.FCA.objects.fund("C523")
        assert 0 == allocation.count()

    def test_fund_allocation_when_fund_invalid(self, populate):
        allocation = self.FCA.objects.fund("C999")
        assert None == allocation

    # Fund Center allocation
    def test_fundcenter_allocation_when_fundcenter_valid_and_allocation_exists(
        self, populate
    ):
        allocation = self.FCA.objects.fundcenter("2184da")
        assert 1 == allocation.count()

    def test_fundcenter_allocation_when_fundcenter_valid_and_no_allocation(
        self, populate
    ):
        allocation = self.FCA.objects.fundcenter("2184BE")
        assert 0 == allocation.count()

    def test_fundcenter_allocation_when_fundcenter_invalid(self, populate):
        allocation = self.FCA.objects.fundcenter("21ZZZ")
        assert None == allocation

    # FY
    def test_fy_allocation_when_allocation_exists(self, populate):
        allocation = self.FCA.objects.fy(2023)
        assert 3 == allocation.count()

    def test_fy_allocation_when_no_allocation(self, populate):
        allocation = self.FCA.objects.fy(3000)
        assert 0 == allocation.count()

    # Quarter
    def test_quarter_allocation_when_allocation_exists(self, populate):
        allocation = self.FCA.objects.quarter(1)
        assert 3 == allocation.count()

    def test_quarter_allocation_when_no_allocation(self, populate):
        allocation = self.FCA.objects.quarter(4)
        assert 0 == allocation.count()

    def test_quarter_allocation_when_quarter_invalid(self, populate):
        allocation = self.FCA.objects.quarter(6)
        assert None == allocation

    def test_descendants_fundcenter_allocation(self, populate):
        allocation = self.FCA.objects.descendants_fundcenter("2184DA")
        assert 3 == allocation.count()

    def test_descendants_costcenter_allocation(self, populate):
        allocation = self.CCA.objects.descendants_costcenter("2184DA")
        assert 2 == allocation.count()

    # Fund and Fund Center
    def test_fundcenter_and_fund_when_allocation_exists(self, populate):
        fc = "2184da"
        fund = None
        allocation = self.FCA.objects.fundcenter(fc).fund(fund)
        assert 1 == allocation.count()


@pytest.mark.django_db
class TestCostCenterAllocationManager:
    @pytest.fixture
    def populate(self):
        self.FCA = CostCenterAllocation
        hnd = populate.Command()
        hnd.handle()

    @pytest.fixture
    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    # Fund Allocations
    def test_fund_allocation_when_fund_valid_and_allocation_exists(self, populate):
        fund_allocation = self.FCA.objects.fund("c113")
        assert 2 == fund_allocation.count()

    # Cost Center Allocations
    def test_fund_allocation_when_fund_valid_and_allocation_exists(self, populate):
        allocation = self.FCA.objects.costcenter("8484wa")
        assert 1 == allocation.count()
