import pytest

from bft.models import BftStatus


@pytest.mark.django_db
class TestModelBftStatus:
    def test_string(self):
        b = BftStatus(status="FY", value=2023)
        assert "FY:2023" == str(b)

    def test_no_fy(self):
        assert None == BftStatus.current.fy()

    def test_no_quarter(self):
        assert None == BftStatus.current.quarter()

    def test_no_period(self):
        assert None == BftStatus.current.period()

    def test_save_entry(self):
        bs = BftStatus()
        bs.status = "FY"
        bs.value = "2023"
        bs.save()
        bs = BftStatus()
        bs.status = "QUARTER"
        bs.value = "1"
        bs.save()
        bs = BftStatus()
        bs.status = "PERIOD"
        bs.value = "1"
        bs.save()

        assert 3 == BftStatus.objects.all().count()
        assert "2023" == BftStatus.current.fy()

    def test_save_quarter_with_invalid_value(self):
        bs = BftStatus()
        bs.status = "QUARTER"
        bs.value = 5
        with pytest.raises(ValueError, match="5 is not a valid period.  Expected value is one of 0, 1, 2, 3, 4"):
            bs.save()

    def test_save_period_with_invalid_value(self):
        bs = BftStatus()
        bs.status = "PERIOD"
        bs.value = 15
        with pytest.raises(
            ValueError,
            match="15 is not a valid period.  Expected value is one of 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14",
        ):
            bs.save()

    def test_save_values_with_invalid_status(self):
        status = {"status": "Y", "value": 2023}
        with pytest.raises(AttributeError, match="Y not a valid status"):
            BftStatus(**status).save()
