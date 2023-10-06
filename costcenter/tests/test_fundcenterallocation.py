import pytest
from costcenter.models import (
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
        a = FundCenterAllocation.objects.create(fundcenter=fc, amount=1000, fy=2023, quarter="1", fund=self.C113)
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
        CostCenterAllocation.objects.create(costcenter=cc, amount=1000, fy=fy, quarter=quarter, fund=self.C113)

        cc = CostCenterManager().cost_center(costcenter="8484XA")
        CostCenterAllocation.objects.create(costcenter=cc, amount=2000, fy=fy, quarter=quarter, fund=self.C113)

        sub_alloc = CostCenterManager().get_sub_alloc(fc, fund, fy, quarter)
        assert 2 == sub_alloc.count()

    def test_get_fundcenter_subordinate_allocation(self, populate):
        da2184 = FundCenterManager().fundcenter(fundcenter="2184DA")
        fc_alloc = FundCenterAllocation.objects.get(fundcenter=da2184, fy=2023, quarter="1", fund=self.C113)

        sub_alloc = FundCenterManager().get_sub_alloc(fc_alloc)
        assert 500 == sub_alloc.aggregate(Sum("amount"))["amount__sum"]
