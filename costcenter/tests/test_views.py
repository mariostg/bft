from django.test import TestCase


class CostCenterPageTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/costcenter/costcenter-table/")
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get("/costcenter/costcenter-table/")
        self.assertTemplateUsed(response, "costcenter/costcenter-table.html")
