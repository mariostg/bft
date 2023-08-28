import pytest
from costcenter.models import FundCenter, FundCenterManager, FundCenterAllocation, Fund
from bft.management.commands import populate
import numpy as np


@pytest.mark.django_db
class TestFundCenterManager:
    @pytest.fixture
    def setup(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        self.current = FundCenter.objects.create(**fc)

    def test_fundcenter(self, setup):
        assert "1111AA" == FundCenterManager().fundcenter("1111aa").fundcenter

    def test_pk(self, setup):
        assert "1111AA" == FundCenterManager().pk(1).fundcenter

    def test_sequence_exists(self, setup):
        assert True == FundCenterManager().sequence_exist("1")

    def test_sequence_does_not_exists(self, setup):
        assert False == FundCenterManager().sequence_exist("11")

    def test_fund_center_exists(self, setup):
        assert True == FundCenterManager().fund_center_exist("1111AA")

    def test_fund_center_does_not_exists(self, setup):
        assert False == FundCenterManager().fund_center_exist("ZZZZZ")

    def test_get_by_fund_center(self, setup):
        obj = FundCenter.objects.fundcenter("1111AA")
        assert "1111AA" == obj.fundcenter

    def test_get_by_pk(self, setup):
        obj = FundCenter.objects.pk(self.current.pk)
        assert obj.pk == self.current.pk

    def test_fund_center_dataframe_empty(self):
        r = FundCenter
        assert 0 == len(r.objects.fund_center_dataframe())

    # Fund Center Tests
    def test_fund_center_dataframe(self):
        hnd = populate.Command()
        hnd.handle()

        r = FundCenter.objects.fund_center_dataframe()

        columns = np.array(r.columns)
        expected_columns = np.array(["fundcenter_id", "Fund Center", "Fund Center Name", "Sequence No", "parent_id"])

        match = (columns == expected_columns).all()
        assert True == match

    def test_fund_center_allocation(self):
        hnd = populate.Command()
        hnd.handle()

        FCM = FundCenterManager()
        fc = FCM.fundcenter(fundcenter="1111aa")
        fund = Fund.objects.get(fund="C113")
        alloc = {"fundcenter": fc, "fund": fund, "fy": 2023, "quarter": "Q0", "amount": 1000}
        FCA = FundCenterAllocation(**alloc)
        FCA.save()

        test_alloc = FCM.allocation(fundcenter="1111AA").first()
        assert alloc["amount"] == test_alloc.amount

    def test_fund_center_allocation_dataframe(self):
        hnd = populate.Command()
        hnd.handle()

        FCM = FundCenterManager()
        fc = FCM.fundcenter(fundcenter="1111aa")
        fund = Fund.objects.get(fund="C113")
        alloc = {"fundcenter": fc, "fund": fund, "fy": 2023, "quarter": "Q0", "amount": 1000}
        FCA = FundCenterAllocation(**alloc)
        FCA.save()

        test_alloc = FCM.allocation_dataframe(fundcenter="1111AA")
        print(test_alloc["Allocation"][0])
        assert alloc["amount"] == test_alloc["Allocation"][0]

    def test_get_direct_descendants(self, setup):
        hnd = populate.Command()
        hnd.handle()
        parent = FundCenterManager().fundcenter(fundcenter="1111AA")
        descendants = FundCenterManager().get_direct_descendants(parent)
        assert 2 == len(descendants)

    def test_get_direct_descendants_empty(self, setup):
        hnd = populate.Command()
        hnd.handle()
        parent = FundCenterManager().fundcenter(fundcenter="2222BB")
        descendants = FundCenterManager().get_direct_descendants(parent)
        assert 0 == len(descendants)

    def test_get_direct_descendants_wrong_string(self, setup):
        hnd = populate.Command()
        hnd.handle()
        assert None == FundCenterManager().get_direct_descendants("2222zz")
