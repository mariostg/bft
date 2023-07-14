import pytest
from costcenter.models import FundCenter, FundCenterManager


@pytest.mark.django_db
class TestFundCenterManager:
    def test_fundcenter(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        FundCenter.objects.create(**fc)
        assert "1111AA" == FundCenterManager().fundcenter("1111aa").fundcenter

    def test_pk(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        FundCenter.objects.create(**fc)
        assert "1111AA" == FundCenterManager().pk(1).fundcenter

    def test_sequence_exists(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        FundCenter.objects.create(**fc)
        assert True == FundCenterManager().sequence_exist("1")

    def test_sequence_does_not_exists(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        FundCenter.objects.create(**fc)
        assert False == FundCenterManager().sequence_exist("11")

    def test_fund_center_exists(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        FundCenter.objects.create(**fc)
        assert True == FundCenterManager().fund_center_exist("1111AA")

    def test_fund_center_does_not_exists(self):
        fc = {"fundcenter": "1111aa", "shortname": "bedroom", "sequence": "1"}
        FundCenter.objects.create(**fc)
        assert False == FundCenterManager().fund_center_exist("ZZZZZ")
