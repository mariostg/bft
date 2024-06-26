from django.test import TestCase

from bft.models import CostCenter, Fund, FundCenter, Source


class CostCenterManagerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        fc = FundCenter.objects.create(fundcenter="2184QQ", fundcenter_parent=None)
        fund = Fund.objects.create(fund="C111", name="Big fund", vote=1, download=True)
        s = Source.objects.create(source="La source")
        obj = CostCenter.objects.create(
            costcenter="8486AA", fund=fund, costcenter_parent=fc, source=s
        )
        cls.pk = obj.pk

    def test_get_by_costcenter(self):
        obj = CostCenter.objects.cost_center("8486AA")
        self.assertEqual("8486AA", obj.costcenter)

    def test_get_by_pk(self):
        obj = CostCenter.objects.pk(self.pk)

        self.assertEqual(obj.pk, self.pk)


class FundManagerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        obj = Fund.objects.create(fund="C111", name="Big fund", vote=1, download=True)
        cls.pk = obj.pk

    def test_get_by_name(self):
        obj = Fund.objects.fund("C111")
        self.assertEqual("C111", obj.fund)

    def test_get_by_pk(self):
        obj = Fund.objects.pk(self.pk)

        self.assertEqual(obj.pk, self.pk)


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
