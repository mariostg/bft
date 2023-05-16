from django.test import TestCase
from costcenter.models import (
    Fund,
    CostCenter,
    Source,
    ForecastAdjustment,
)
from django.db import IntegrityError


class FundModelTest(TestCase):
    fund_c113 = {"fund": "C113", "name": "National Procurement", "vote": "1"}
    fund_c523 = {"fund": "C523", "name": "Project National Procurement", "vote": "5"}
    fund_X999 = {"fund": "X999", "name": "Undesired Fund", "vote": "1"}

    def test_string_representation(self):
        fund = Fund(fund="C113", name="NP Capital", vote=1)
        self.assertEqual(str(fund), "C113 - NP Capital")

    def test_verbose_name_plural(self):
        self.assertEqual(str(Fund._meta.verbose_name_plural), "Funds")

    def test_can_save_and_retrieve_funds(self):
        first_fund = Fund()
        first_fund.fund = "c113"
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
        response = self.client.post("/fund/add/", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Fund.objects.count(), 1)
        new_fund = Fund.objects.first()
        self.assertEqual(new_fund.fund, "C113")

    def test_can_update_fund_column_values(self):
        f0 = Fund(**self.fund_c113)
        f0.save()

        f1 = Fund.objects.filter(fund="C113").first()
        f1.fund = "X999"
        f1.name = "New Name"
        f1.vote = 4
        f1.save()

        f2 = Fund.objects.filter(pk=f1.pk).first()
        self.assertEqual("X999", f2.fund)
        self.assertEqual("New Name", f2.name)
        self.assertEqual("4", f2.vote)

    def test_can_delete_fund(self):
        f0 = Fund(**self.fund_c113)
        f0.save()

        f1 = Fund.objects.get(pk=f0.id)
        f1.delete()

        self.assertEqual(0, Fund.objects.count())


class SourceModelTest(TestCase):
    def test_string_representation(self):
        obj = Source(source="Bedroom")
        self.assertEqual(str(obj), "Bedroom")

    def test_verbose_name_plural(self):
        self.assertEqual(str(Source._meta.verbose_name_plural), "Sources")

    def test_can_save_and_retrieve_sources(self):
        first_source = Source()
        first_source.source = "Primary"
        first_source.save()

        first_source = Source()
        first_source.source = "Secondary"
        first_source.save()

        saved_sources = Source.objects.all()
        first_saved_source = saved_sources[0]
        second_saved_source = saved_sources[1]
        self.assertEqual("Primary", first_saved_source.source)
        self.assertEqual("Secondary", second_saved_source.source)

    def test_source_cannot_be_saved_twice(self):
        Source.objects.all().delete()

        source_1 = Source()
        source_1.source = "Primary"
        source_1.save()

        source_2 = Source()
        source_2.source = "Primary"

        with self.assertRaises(IntegrityError):
            source_2.save()

    def test_can_save_POST_request(self):
        data = {"source": "Ternaire"}
        response = self.client.post("/source/source-add/", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Source.objects.count(), 1)
        new_source = Source.objects.first()
        self.assertEqual(new_source.source, "Ternaire")


class ForecastAdjustmentModelTest(TestCase):
    def test_string_representation(self):
        fund = Fund(fund="C113", name="NP", vote=1)
        cc = CostCenter(costcenter="8484WA", shortname="Kitchen", fund=fund)
        obj = ForecastAdjustment(costcenter=cc, fund=fund, amount=1000)
        self.assertEqual(str(obj), "8484WA - Kitchen - C113 - NP - 1000")

    def test_verbose_name_plural(self):
        self.assertEqual(str(ForecastAdjustment._meta.verbose_name_plural), "Forecast Adjustments")
