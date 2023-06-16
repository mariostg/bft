from django.test import TestCase
from costcenter.models import Source


class SourceManagerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        s = Source.objects.create(source="La source")
        cls.pk = s.pk

    def test_get_by_name(self):
        s = Source.objects.source("La source")

        self.assertEqual("La source", s.source)

    def test_get_by_pk(self):
        s = Source.objects.pk(self.pk)

        self.assertEqual(s.pk, self.pk)
