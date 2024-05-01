from io import StringIO

import pytest
from django.core.management import call_command
from bft.models import LineItemManager, LineItem, CostCenterManager
from reports.models import CostCenterMonthly

@pytest.mark.django_db
class TestCommandMonthlyData:

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

    def test_bftstatus(self):
        out = self.call_command("monthlydata", "--bftstatus")
        assert True == ("Current fiscal year" in out)
        assert True == ("Current quarter" in out)
        assert True == ("Current period" in out)

    def test_running_monthlydata_has_lines(self):
        """Check that executing monthly data for given fy, period, contains the cost center and number of lines expected."""
        self.call_command("populate")
        self.call_command("uploadcsv", "test-data/encumbrance_2184A3.txt")

        ccmgr = CostCenterManager()
        assert ccmgr.exists("8484WA") == True
        assert 7 == LineItem.objects.count()

        self.call_command("monthlydata", "--update", "--fy", "2023", "--period", "1")
        assert 2 == CostCenterMonthly.objects.count()
