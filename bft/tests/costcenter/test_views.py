from django.test import TestCase
from django.urls import reverse


class CostCenterPageTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/costcenter/costcenter-table/")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("costcenter-table"))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get("/costcenter/costcenter-table/")
        self.assertTemplateUsed(response, "costcenter/costcenter-table.html")


class CostCenterAddTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/costcenter/costcenter-add/")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("costcenter-add"))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("costcenter-add"))
        self.assertTemplateUsed(response, "costcenter/costcenter-form.html")


class CostCenterUpdateTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/costcenter/costcenter-update/1")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("costcenter-update", args=[1]))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("costcenter-table"))
        self.assertTemplateUsed(response, "costcenter/costcenter-table.html")


"""
Testing Source urls and templates.
"""


class SourcePageTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/source/source-table/")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("source-table"))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("source-table"))
        self.assertTemplateUsed(response, "costcenter/source-table.html")


class SourceAddTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/source/source-add/")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("source-add"))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("source-add"))
        self.assertTemplateUsed(response, "costcenter/source-form.html")


class SourceUpdateTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/source/source-update/1/")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("source-update", args=[1]))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("source-update", args=[1]))
        self.assertTemplateUsed(response, "costcenter/source-form.html")


class SourceDeleteTest(TestCase):
    def test_url_is_good(self):
        response = self.client.get("/source/source-delete/1/")
        self.assertEqual(200, response.status_code)

    def test_url_by_name(self):
        response = self.client.get(reverse("source-delete", args=[1]))
        self.assertEqual(200, response.status_code)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("source-delete", args=[1]))
        self.assertTemplateUsed(response, "core/delete-object.html")
