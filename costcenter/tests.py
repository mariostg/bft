from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from costcenter.views import fund_page


class FundPageTest(TestCase):
    def test_fund_url_resolved_to_fund_page_view(self):
        found = resolve("/fund/fund_page/")
        self.assertEqual(found.func, fund_page)

    def test_fund_page_returns_correct_html(self):
        request = HttpRequest()
        response = fund_page(request)
        html = response.content.decode("utf8")
        self.assertTrue(html.startswith("<html>"))
        self.assertIn("<title>Fund List</title>", html)
        self.assertTrue(html.endswith("</html>"))
