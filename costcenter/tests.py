from django.test import TestCase
from django.urls import resolve
from costcenter.views import fund_page


class FundPageTest(TestCase):
    def testfund_url_resolved_to_fund_page_view(self):
        found = resolve("/fund/fund_page/")
        self.assertEqual(found.func, fund_page)
