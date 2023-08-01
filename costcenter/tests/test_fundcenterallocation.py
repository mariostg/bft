import pytest
from costcenter.models import CostCenterAllocation, FundCenterManager, FundCenterAllocation, Fund, CostCenterManager
from encumbrance.management.commands import populate, uploadcsv


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
        a = FundCenterAllocation.objects.create(fundcenter=fc, amount=1000, fy=2023, quarter="Q1", fund=self.C113)
        assert 1 == a.id

    def test_get_subordinate_allocation(self, setup):
        fc = FundCenterManager().fundcenter("1111ab")
        fc_alloc = FundCenterAllocation.objects.create(
            fundcenter=fc, amount=1000, fy=2023, quarter="Q1", fund=self.C113
        )
        assert 1 == fc_alloc.id

        cc = CostCenterManager().cost_center(costcenter="8486C1")
        CostCenterAllocation.objects.create(costcenter=cc, amount=1000, fy=2023, quarter="Q1", fund=self.C113)

        cc = CostCenterManager().cost_center(costcenter="8486C2")
        CostCenterAllocation.objects.create(costcenter=cc, amount=2000, fy=2023, quarter="Q1", fund=self.C113)

        sub_alloc = FundCenterManager().get_sub_alloc(fc_alloc)
