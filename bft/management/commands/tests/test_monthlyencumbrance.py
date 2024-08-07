import re
from io import StringIO

import pytest
from django.core.management import call_command

from bft.models import CostCenterManager, LineItem
from reports.models import CostCenterMonthlyEncumbrance


@pytest.mark.django_db
class TestCommandMonthlyEncumbrance:

    def call_command(self, command, *args, **kwargs):
        out = StringIO()
        call_command(
            command,
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_running_monthlyencumbrance_has_lines(self):
        """Check that executing monthly data for given fy, period, contains the cost center and number of lines expected."""
        self.call_command("populate")
        self.call_command("uploadcsv", "test-data/encumbrance_2184A3.txt")

        ccmgr = CostCenterManager()
        assert ccmgr.cost_center("8484WA").isupdatable
        assert ccmgr.exists("8484WA") == True
        assert 7 == LineItem.objects.count()

        self.call_command("monthlyencumbrance", "--update", "--fy", "2023", "--period", "1")
        assert 2 == CostCenterMonthlyEncumbrance.objects.count()

    def test_monthlyencumbrance_view_invalid_period(self):
        self.call_command("populate")
        self.call_command("uploadcsv", "test-data/encumbrance_2184A3.txt")

        ccmgr = CostCenterManager()
        assert ccmgr.cost_center("8484WA").isupdatable
        assert ccmgr.exists("8484WA") == True
        assert 7 == LineItem.objects.count()
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Period [19] not valid.  Must be one of ('1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14')"
            ),
        ):
            self.call_command("monthlyencumbrance", "--view", "--period", "19")

    def test_monthlyencumbrance_view_with_period_only(self):
        self.call_command("populate")
        self.call_command("uploadcsv", "test-data/encumbrance_2184A3.txt")

        ccmgr = CostCenterManager()
        assert ccmgr.exists("8484WA") == True
        assert 7 == LineItem.objects.count()

        try:
            self.call_command("monthlyencumbrance", "--view", "--period", "1")
        except Exception as exc:
            pytest.fail(f"Using --view with period only as param fails with exception {exc}")
