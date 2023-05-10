from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest
from django.db import IntegrityError
from costcenter.views import fund_page, fund_add, fund_update
from costcenter.models import Fund, Source


def strip_white_space(string: str):
    return string.replace("\t", "").replace("\n", "")


class FundPageTest(TestCase):
    def test_use_fund_page_template(self):
        response = self.client.get("/fund/table/")
        self.assertTemplateUsed(response, "costcenter/fund-table.html")

    def test_fund_url_resolved_to_fund_page_view(self):
        found = resolve("/fund/table/")
        self.assertEqual(found.func, fund_page)

    def test_fund_page_returns_correct_html(self):
        request = HttpRequest()
        response = fund_page(request)
        html = strip_white_space(response.content.decode("utf8"))
        # print(html)
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<caption>Funds</caption>", html)


class FundCreatePageTest(TestCase):
    def test_use_fund_form_template(self):
        response = self.client.get("/fund/add/")
        self.assertTemplateUsed(response, "costcenter/fund-form.html")

    def test_fund_add_url_resolves_to_fund_form_view(self):
        found = resolve("/fund/add/")
        print(found)
        self.assertEqual(found.func, fund_add)

    def test_fund_create_returns_correct_html(self):
        request = HttpRequest()
        response = fund_add(request)
        html = strip_white_space(response.content.decode("utf8"))
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn('<h1 class="form__header">Fund Entry Form</h1>', html)


class FundUpdatePageTest(TestCase):
    def test_use_fund_form_template(self):
        Fund.objects.create(fund="X333", name="Test fund update", vote="1")
        f = Fund.objects.get(fund="X333")
        response = self.client.get(f"/fund/update/{f.pk}/")
        self.assertTemplateUsed(response, "costcenter/fund-form.html")

    def test_fund_update_url_resolves_to_fund_form_view(self):
        Fund.objects.create(fund="X111", name="Test fund update", vote="1")
        f = Fund.objects.get(fund="X111")
        found = resolve(f"/fund/update/{f.pk}/")
        self.assertEqual(found.func, fund_update)
