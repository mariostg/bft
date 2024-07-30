import numpy as np
import pytest

from bft.models import Fund, FundCenter, FundCenterManager


@pytest.mark.django_db
class TestFundCenterManager:
    @pytest.fixture
    def setup(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        self.current = FundCenter.objects.create(**fc)
        fund = {"fund": "C113"}
        Fund.objects.create(**fund)

    def test_fundcenter(self, setup):
        assert "1111AA" == FundCenterManager().fundcenter("1111aa").fundcenter

    def test_pk(self, setup):
        assert "1111AA" == FundCenterManager().pk(1).fundcenter

    def test_sequence_exists(self, setup):
        assert True == FundCenterManager().sequence_exist("1")

    def test_sequence_does_not_exists(self):
        assert False == FundCenterManager().sequence_exist("11")

    def test_get_by_fund_center(self, setup):
        obj = FundCenter.objects.fundcenter("1111AA")
        assert "1111AA" == obj.fundcenter

    def test_get_by_pk(self, setup):
        obj = FundCenter.objects.pk(self.current.pk)
        assert obj.pk == self.current.pk

    def test_fund_center_dataframe_empty(self):
        r = FundCenter
        assert 0 == len(r.objects.fund_center_dataframe(r.objects))

    def test_a_given_fund_center_does_not_exists(self):
        assert False == FundCenterManager().exists("9999aa")

    def test_fund_center_has_data(self, setup):
        FundCenterManager().exists()
        assert True == FundCenterManager().exists()

    # Fund Center Tests
    def test_fund_center_dataframe(self, populatedata):
        fc = FundCenter
        r = FundCenterManager().fund_center_dataframe(fc.objects.all())

        columns = np.array(r.columns)
        expected_columns = np.array(
            [
                "Fundcenter_ID",
                "Fund Center",
                "Fund Center Name",
                "FC Path",
                "Level",
                "Fundcenter_parent_ID",
            ]
        )

        match = (columns == expected_columns).all()
        assert True == match

    def test_get_direct_descendants(self, populatedata):
        parent = FundCenterManager().fundcenter(fundcenter="2184DA")
        descendants = FundCenterManager().get_direct_descendants(parent)
        assert 3 == len(descendants)

    def test_get_direct_descendants_empty(self):
        parent = FundCenterManager().fundcenter(fundcenter="2222BB")
        descendants = FundCenterManager().get_direct_descendants(parent)
        assert 0 == len(descendants)

    def test_get_direct_descendants_wrong_string(self, populatedata):
        assert FundCenterManager().get_direct_descendants("2222zz") is None
