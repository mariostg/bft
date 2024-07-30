import pytest
from django.http import HttpRequest
from django.test import Client
from django.urls import resolve
from pytest_django.asserts import assertTemplateUsed

from bft.models import Fund
from bft.views.costcenter import fund_add, fund_page, fund_update
from utils.string import strip_white_space


@pytest.mark.django_db
class TestFundPage:
    def test_use_fund_page_template(self):
        response = Client().get("/fund/fund-table/")
        assertTemplateUsed(response, "costcenter/fund-table.html")

    def test_fund_url_resolved_to_fund_page_view(self):
        found = resolve("/fund/fund-table/")
        assert found.func == fund_page

    def test_fund_page_returns_correct_html(self):
        request = HttpRequest()
        response = fund_page(request)
        html = strip_white_space(response.content.decode("utf8"))
        # print(html)
        assert html.startswith("<!DOCTYPE html>")
        assert "<h2>Funds</h2>" in html


class TestFundCreatePage:
    def test_use_fund_form_template(self):
        response = Client().get("/fund/fund-add/")
        assertTemplateUsed(response, "costcenter/fund-form.html")

    def test_fund_add_url_resolves_to_fund_form_view(self):
        found = resolve("/fund/fund-add/")
        assert found.func == fund_add

    def test_fund_create_returns_correct_html(self):
        request = HttpRequest()
        response = fund_add(request)
        html = strip_white_space(response.content.decode("utf8"))
        assert html.startswith("<!DOCTYPE html>")
        assert "<header class='form__header'>Fund Entry Form</header>" in html


@pytest.mark.django_db
class TestFundUpdatePage:
    def test_use_fund_form_template(self):
        Fund.objects.create(fund="X333", name="Test fund update", vote="1")
        f = Fund.objects.get(fund="X333")
        response = Client().get(f"/fund/fund-update/{f.pk}/")
        assertTemplateUsed(response, "costcenter/fund-form.html")

    def test_fund_update_url_resolves_to_fund_form_view(self):
        Fund.objects.create(fund="X111", name="Test fund update", vote="1")
        f = Fund.objects.get(fund="X111")
        found = resolve(f"/fund/fund-update/{f.pk}/")
        assert found.func == fund_update
