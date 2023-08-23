import pytest
from bft.models import BftStatus


@pytest.mark.django_db
class TestModelBftStatus:
    def test_string(self):
        b = BftStatus(status="FY", value=2023)
        assert "FY:2023" == str(b)

    def test_save_entry(self):
        bs = BftStatus()
        bs.status = "FY"
        bs.save()
        bs = BftStatus()
        bs.status = "QUARTER"
        bs.save()

        assert 2 == BftStatus.objects.all().count()

    def test_save_values_with_invalid_choices(self):
        status = {"status": "Y", "value": 2023}
        with pytest.raises(AttributeError, match="Y not a valid status"):
            BftStatus(**status).save()
