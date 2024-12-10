import pytest
from django.test import Client
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.django_db
class TestCostCenterPageTest:
    def test_url_is_good(self):
        response = Client().get("/costcenter/costcenter-table/")
        assert 200 == response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("costcenter-table"))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get("/costcenter/costcenter-table/")
        assertTemplateUsed(response, "costcenter/costcenter-table.html")


@pytest.mark.django_db
class TestCostCenterAdd:
    def test_url_is_good(self):
        response = Client().get("/costcenter/costcenter-add/")
        assert 200 == response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("costcenter-add"))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get(reverse("costcenter-add"))
        assertTemplateUsed(response, "costcenter/costcenter-form.html")


@pytest.mark.django_db
class TestCostCenterUpdate:
    def test_url_is_good(self):
        response = Client().get("/costcenter/costcenter-update/1")
        assert 200, response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("costcenter-update", args=[1]))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get(reverse("costcenter-table"))
        assertTemplateUsed(response, "costcenter/costcenter-table.html")


@pytest.mark.django_db
class TestFundAdd:
    def test_add_fund(self):
        c = Client()
        response = c.post(
            "/fund/fund-add/",
            {"fund": "c113", "name": "the name", "vote": "1"},
        )
        assert 302 == response.status_code
        response = c.post(
            "/fund/fund-add/",
            {"fund": "c113", "name": "the name", "vote": "1"},
        )
        assert "Fund C113" in str(response.content)

    def test_invalid_fund(self):
        c = Client()
        response = c.post(
            "/fund/fund-add/",
            {"fund": "113", "name": "the name", "vote": "1"},
        )
        assert "Fund must begin with a letter" in str(response.content)

    def test_invalid_vote(self):
        c = Client()
        response = c.post(
            "/fund/fund-add/",
            {"fund": "C114", "name": "the name", "vote": "8"},
        )
        assert "Vote must be 1 or 5" in str(response.content)


"""
Testing Source urls and templates.
"""


@pytest.mark.django_db
class TestSourcePage:
    def test_url_is_good(self):
        response = Client().get("/source/source-table/")
        assert 200 == response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("source-table"))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get(reverse("source-table"))
        assertTemplateUsed(response, "costcenter/source-table.html")


@pytest.mark.django_db
class TestSourceAdd:
    def test_url_is_good(self):
        response = Client().get("/source/source-add/")
        assert 200 == response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("source-add"))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get(reverse("source-add"))
        assertTemplateUsed(response, "costcenter/source-form.html")

    def test_add_source(self):
        c = Client()
        response = c.post("/source/source-add/", {"source": "AAAA"})
        assert 302 == response.status_code
        response = c.post("/source/source-add/", {"source": "AAAA"})
        assert "Source Aaaa" in str(response.content)


@pytest.mark.django_db
class TestSourceUpdate:
    def test_url_is_good(self):
        response = Client().get("/source/source-update/1/")
        assert 200 == response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("source-update", args=[1]))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get(reverse("source-update", args=[1]))
        assertTemplateUsed(response, "costcenter/source-form.html")


@pytest.mark.django_db
class TestSourceDelete:
    def test_url_is_good(self):
        response = Client().get("/source/source-delete/1/")
        assert 200 == response.status_code

    def test_url_by_name(self):
        response = Client().get(reverse("source-delete", args=[1]))
        assert 200 == response.status_code

    def test_view_uses_correct_template(self):
        response = Client().get(reverse("source-delete", args=[1]))
        assertTemplateUsed(response, "core/delete-object.html")
