from django.test import Client, TestCase

from bft.management.commands.uploadcsv import Command
import bft.management.commands.populate as populate


class CostCenterLineItemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        print("Setting up")
        filldata = populate.Command()
        filldata.handle()
        a = Command()
        a.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_url_is_good(self):
        c = Client()
        response = c.get("/lineitem/costcenter/8484WA/")
        self.assertEqual(200, response.status_code)

    def test_url_is_bad(self):
        c = Client()
        response = c.get("/lineitem/costcenter/1111/")
        # self.assertEqual(404, response.status_code)
        assert True == ("There appears to be no line items in 1111" in str(response.content))

    def test_view_uses_correct_template(self):
        response = self.client.get("/lineitem/costcenter/8484WA/")
        self.assertTemplateUsed(response, "lineitems/lineitem-table.html")

    def test_cost_center_line_items_has_lines(self):
        c = Client()
        response = c.get("/lineitem/costcenter/8484WA/")
        self.assertEqual(200, response.status_code)
        self.assertGreater(len(response.context["data"]), 0)
