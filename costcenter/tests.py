from django.test import TestCase
from django.urls import resolve
from django.http import HttpRequest
from django.db import IntegrityError
from costcenter.views import fund_page, fund_add, fund_update
from costcenter.models import Fund


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


class FundModelTest(TestCase):
    fund_c113 = {"fund": "C113", "name": "National Procurement", "vote": "1"}
    fund_c523 = {"fund": "C523", "name": "Project National Procurement", "vote": "5"}
    fund_X999 = {"fund": "X999", "name": "Undesired Fund", "vote": "1"}

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

    def test_fund_cannot_be_saved_twice(self):
        fund_1 = Fund()
        fund_1.fund = "C113"
        fund_1.name = "National procurement"
        fund_1.vote = "1"
        fund_1.download = True
        fund_1.save()

        fund_2 = Fund()
        fund_2.fund = "C113"
        fund_2.name = "Not an interesting fund"
        fund_2.vote = "5"
        fund_2.download = False
        with self.assertRaises(IntegrityError):
            fund_2.save()

    def test_can_save_POST_request(self):
        data = {"fund": "C113", "name": "National Procurement", "vote": "1"}
        response = self.client.post("/fund/new/", data=data)
        print(response)
        # self.assertEqual(Fund.objects.count(), 1)
        # new_fund = Fund.objects.first()
        # self.assertEqual(new_fund.fund, "C113")

        # self.assertIn('A new list item', response.content.decode())
        # self.assertTemplateUsed(response, 'home.html')

    def test_can_update_fund_column_values(self):
        f0 = Fund(**self.fund_c113)
        f0.save()

        f1 = Fund.objects.filter(fund="C113").first()
        f1.fund = "X999"
        f1.name = "New Name"
        f1.vote = 4
        f1.save()

        f2 = Fund.objects.filter(pk=f1.pk).first()
        self.assertEqual("X999", f1.fund)
        self.assertEqual("New Name", f1.name)
        self.assertEqual(4, f1.vote)

    def test_can_delete_fund(self):
        f0 = Fund(**self.fund_c113)
        f0.save()

        f1 = Fund.objects.get(pk=f0.id)
        f1.delete()

        self.assertEqual(0, Fund.objects.count())
