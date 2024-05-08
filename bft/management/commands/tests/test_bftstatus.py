from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
class TestBftStatus:
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
        out = self.call_command("bftstatus")
        assert True == ("Current fiscal year" in out)
        assert True == ("Current quarter" in out)
        assert True == ("Current period" in out)
