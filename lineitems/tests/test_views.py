from django.test import Client, TestCase

from encumbrance.management.commands.uploadcsv import Command
import encumbrance.management.commands.populate as populate


class CostCenterLineItemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        print("Setting up")
        filldata = populate.Command()
        filldata.handle()
        a = Command()
        a.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

    def test_url_is_good(self):
        c = Client()
        response = c.get("/lineitem/costcenter/8486B1/")
        self.assertEqual(200, response.status_code)

    def test_url_is_bad(self):
        c = Client()
        response = c.get("/lineitem/costcenter/1111/")
        self.assertEqual(404, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get("/lineitem/costcenter/8486B1/")
        self.assertTemplateUsed(response, "lineitems/lineitem-table.html")

    def test_cost_center_line_items_has_lines(self):
        # there are 5 lines for 8486B1 in encumbrance_tiny.txt
        c = Client()
        response = c.get("/lineitem/costcenter/8486B1/")
        self.assertEqual(200, response.status_code)
        self.assertEqual(len(response.context["data"]), 5)
