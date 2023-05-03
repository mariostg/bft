from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest

from costcenter.views import fund_page
from costcenter.models import Fund


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


class FundModelTest(TestCase):
    def test_can_save_and_retrieve_funds(self):
        first_fund = Fund()
        first_fund.fund = "C113"
        first_fund.name = "National procurement"
        first_fund.vote = "1"
        first_fund.download = True
        first_fund.save()

        first_fund = Fund()
        first_fund.fund = "X999"
        first_fund.name = "Not an interesting fund"
        first_fund.vote = "5"
        first_fund.download = False
        first_fund.save()

        saved_funds = Fund.objects.all()
        first_saved_fund = saved_funds[0]
        second_saved_fund = saved_funds[1]
        self.assertEqual("C113", first_saved_fund.fund)
        self.assertEqual("X999", second_saved_fund.fund)
