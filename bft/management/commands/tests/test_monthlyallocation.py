from io import StringIO

import pytest
from django.core.management import call_command

from bft.models import CostCenterAllocation
from reports.models import CostCenterMonthlyAllocation


@pytest.mark.django_db
class TestCommandMonthlyAllocation:

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

    def test_running_monthlyallocation_has_lines(self):
        """Check that executing monthly data for given fy, period, contains the cost center and number of lines expected."""
        self.call_command("populate")

        assert 2 == CostCenterAllocation.objects.count()

        self.call_command("monthlyallocation", "--update", "--fy", "2023", "--period", "1", "--quarter", "1")
        assert 2 == CostCenterMonthlyAllocation.objects.count()
