import pytest
from costcenter.models import FundCenter, FundCenterManager


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
