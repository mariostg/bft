from io import StringIO

import pytest
from django.core.management import call_command

from bft.management.commands.monthlydata import Command


@pytest.mark.django_db
class TestCommandMonthlyData:
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "monthlydata",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test_bftstatus(self):
        out = self.call_command("--bftstatus")
        assert True == ("Current fiscal year" in out)
        assert True == ("Current quarter" in out)
        assert True == ("Current period" in out)
