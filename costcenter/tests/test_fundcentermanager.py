import pytest
from costcenter.models import FundCenter, FundCenterManager, FundCenterAllocation, Fund
from bft.management.commands import populate
import numpy as np
from django.db.models import QuerySet


@pytest.mark.django_db
class TestFundCenterManager:
    @pytest.fixture
    def setup(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        self.current = FundCenter.objects.create(**fc)
        fund = {"fund": "C113"}
        Fund.objects.create(**fund)

    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

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
        assert 0 == len(r.objects.fund_center_dataframe(r.objects))

    # Fund Center Tests
    def test_fund_center_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        fc = FundCenter
        r = FundCenterManager().fund_center_dataframe(fc.objects.all())

        columns = np.array(r.columns)
        expected_columns = np.array(
            ["Fundcenter_ID", "Fund Center", "Fund Center Name", "FC Path", "Fundcenter_parent_ID"]
        )

        match = (columns == expected_columns).all()
        assert True == match

    def test_fund_center_manager_allocation(self, setup):
        FCM = FundCenterManager()
        fc = FCM.fundcenter(fundcenter="1111aa")
        fund = Fund.objects.get(fund="C113")
        alloc = {"fundcenter": fc, "fund": fund, "fy": 2023, "quarter": 0, "amount": 1000}
        FCA = FundCenterAllocation(**alloc)
        FCA.save()

        test_alloc = FCM.allocation(fundcenter="1111AA")
        assert alloc["amount"] == test_alloc.amount

    def test_fund_center_manager_allocation_non_existing_fund(self, populate):
        alloc = FundCenterManager().allocation(fund="C999")
        print(alloc)
        assert 0 == alloc.amount

    def test_fund_center_manager_allocation_from_fc_list(self, populate):
        fc = ["2184DA", "2184A3"]
        data = FundCenter.objects.allocation(fundcenter=fc, fund="c113", fy=2023, quarter=1)

        assert 2 == len(data)
        assert data[0].amount == 1000
        assert data[1].amount == 500

    def test_fund_center_manager_without_allocation(self, setup):
        FCM = FundCenterManager()
        test_alloc = FCM.allocation(fundcenter="1111AA")
        assert True == isinstance(test_alloc, FundCenterAllocation)
        assert 0 == test_alloc.amount

    def test_fund_center_allocation_dataframe(self, setup):
        FCM = FundCenterManager()
        fc = FCM.fundcenter(fundcenter="1111aa")
        fund = Fund.objects.get(fund="C113")
        alloc = {"fundcenter": fc, "fund": fund, "fy": 2023, "quarter": 0, "amount": 1000}
        FCA = FundCenterAllocation(**alloc)
        FCA.save()

        test_alloc = FCM.allocation_dataframe(fundcenter="1111AA")
        assert alloc["amount"] == test_alloc["Allocation"][0]

    def test_get_direct_descendants(self):
        hnd = populate.Command()
        hnd.handle()
        parent = FundCenterManager().fundcenter(fundcenter="2184DA")
        descendants = FundCenterManager().get_direct_descendants(parent)
        assert 6 == len(descendants)

    def test_get_direct_descendants_empty(self, setup):
        parent = FundCenterManager().fundcenter(fundcenter="2222BB")
        descendants = FundCenterManager().get_direct_descendants(parent)
        assert 0 == len(descendants)

    def test_get_direct_descendants_wrong_string(self, setup):
        hnd = populate.Command()
        hnd.handle()
        assert None == FundCenterManager().get_direct_descendants("2222zz")
