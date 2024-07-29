import pytest
from django.test import Client

import bft.management.commands.populate as populate
from bft.management.commands.uploadcsv import Command
from bft.models import CostCenter


class CostCenterLineItemTest:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_url_is_good(self, populate):
        c = Client()
        cc_id = CostCenter.objects.cost_center("8484wa").id
        response = c.get(f"/bft/lineitem/?costcenter={cc_id}")
        self.assertEqual(200, response.status_code)
