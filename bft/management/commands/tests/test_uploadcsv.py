from io import StringIO

import pytest
from django.core.management import call_command
from bft.models import LineItemManager, LineItem, CostCenterManager


@pytest.mark.django_db
class TestCommandUploadCsv:
    def call_command(self, command, *args, **kwargs):
        call_command(
            command,
            *args,
            **kwargs,
        )

    def test_running_uploadcsv_has_lines(self):
        """Check that uploaded lines contains the cost center and number of lines expected."""
        self.call_command("populate")
        ccmgr = CostCenterManager()
        assert ccmgr.exists("8484WA") == True
        self.call_command("uploadcsv", "test-data/encumbrance_2184A3.txt")
        mgr = LineItemManager()
        assert mgr.has_line_items(ccmgr.cost_center("8484wa"))
        assert 7 == LineItem.objects.count()
