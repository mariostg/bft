from django.test import Client, TestCase

import bft.management.commands.populate as populate
from bft.management.commands.uploadcsv import Command
from bft.models import CostCenter


class CostCenterLineItemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        filldata = populate.Command()
        filldata.handle()
        a = Command()
        a.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")
        cls.cc_id = CostCenter.objects.cost_center("8484wa").id

    def test_url_is_good(self):
        c = Client()
        response = c.get(f"/bft/lineitem/?costcenter={self.cc_id}")
        self.assertEqual(200, response.status_code)
