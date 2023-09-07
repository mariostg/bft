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
    def setup(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        self.C113 = Fund.objects.get(fund="C113")

    def test_create_fund_center_allocation(self, setup):

        fc = FundCenterManager().fundcenter("1111ab")
        a = FundCenterAllocation.objects.create(fundcenter=fc, amount=1000, fy=2023, quarter="1", fund=self.C113)
        assert a.fundcenter.fundcenter == "1111AB"

    def test_get_costcenter_subordinate_allocation(self, setup):
        FundCenterAllocation.objects.all().delete()
        CostCenterAllocation.objects.all().delete()
        fc = FundCenterManager().fundcenter("1111AB")
        fund = FundManager().fund("C113")
        fc_alloc = FundCenterAllocation.objects.create(fundcenter=fc, amount=1000, fy=2023, quarter="1", fund=self.C113)
        assert "1111AB" == fc_alloc.fundcenter.fundcenter

        cc = CostCenterManager().cost_center(costcenter="8486C1")
        CostCenterAllocation.objects.create(costcenter=cc, amount=1000, fy=2023, quarter="1", fund=self.C113)

        cc = CostCenterManager().cost_center(costcenter="8486C2")
        CostCenterAllocation.objects.create(costcenter=cc, amount=2000, fy=2023, quarter="1", fund=self.C113)

        fc_alloc = FundCenterAllocation(fundcenter=fc, fund=fund, fy=2023, quarter=1)
        sub_alloc = CostCenterManager().get_sub_alloc(fc_alloc)
        assert 2 == sub_alloc.count()

    def test_get_fundcenter_subordinate_allocation(self, setup):
        FundCenterAllocation.objects.all().delete()
        fc = FundCenterManager().fundcenter("1111AA")
        fc_alloc = FundCenterAllocation.objects.create(fundcenter=fc, amount=1000, fy=2023, quarter="1", fund=self.C113)
        assert "1111AA" == fc_alloc.fundcenter.fundcenter

        cc = FundCenterManager().fundcenter(fundcenter="1111AB")
        FundCenterAllocation.objects.create(fundcenter=cc, amount=1000, fy=2023, quarter="1", fund=self.C113)

        cc = FundCenterManager().fundcenter(fundcenter="1111AC")
        FundCenterAllocation.objects.create(fundcenter=cc, amount=2000, fy=2023, quarter="1", fund=self.C113)

        sub_alloc = FundCenterManager().get_sub_alloc(fc_alloc)
        assert 3000 == sub_alloc.aggregate(Sum("amount"))["amount__sum"]
