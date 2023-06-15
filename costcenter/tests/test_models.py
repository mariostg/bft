from django.test import TestCase
from costcenter.models import (
    Fund,
    CostCenter,
    Source,
    ForecastAdjustment,
    FundCenter,
    CostCenterAllocation,
)
from django.db import IntegrityError
from django.db.models import RestrictedError
from bft.exceptions import (
    InvalidAllocationException,
    InvalidOptionException,
    InvalidFiscalYearException,
)

FUND_C113 = {"fund": "C113", "name": "National Procurement", "vote": "1"}
SOURCE_1 = {"source": "Kitchen"}
FC_1111AA = {"fundcenter": "1111aa", "shortname": "bedroom", "parent": None}
CC_1234FF = {
    "costcenter": "1234ff",
    "shortname": "Food and drink",
    "fund": None,
    "source": None,
    "isforecastable": True,
    "isupdatable": True,
    "note": "A quick and short note for 1234FF",
    "parent": None,
}


class FundModelTest(TestCase):
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

    def test_saved_fund_is_capitalized(self):
        f = Fund()
        f.fund = "c113"
        f.name = "National procurement"
        f.vote = "1"
        f.download = True
        f.save()

        saved = Fund.objects.get(pk=f.pk)
        self.assertEqual("C113", saved.fund)

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
        data = {
            "fund": "C113",
            "name": "National Procurement",
            "vote": "1",
            "download": True,
        }
        response = self.client.post("/fund/fund-add/", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Fund.objects.count(), 1)
        new_fund = Fund.objects.first()
        self.assertEqual(new_fund.fund, "C113")

    def test_can_delete_POST_request(self):
        data = {
            "fund": "C999",
            "name": "National Procurement",
            "vote": "1",
            "download": True,
        }
        fund = Fund.objects.create(**data)

        response = self.client.post(f"/fund/fund-delete/{fund.id}")
        self.assertEqual(response.status_code, 301)  # redirect to confirm page

    def test_can_update_fund_column_values(self):
        f0 = Fund(**FUND_C113)
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
        f0 = Fund(**FUND_C113)
        f0.save()

        f1 = Fund.objects.get(pk=f0.id)
        f1.delete()

        self.assertEqual(0, Fund.objects.count())

    def test_delete_fund_with_cc_raises_restricted_error(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.parent = parent
        f0.save()

        with self.assertRaises(RestrictedError):
            fund.delete()


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

    def test_saved_source_is_capitalized(self):
        s = Source(source="my source")
        s.save()

        saved = Source.objects.get(pk=s.pk)
        self.assertEqual("My source", saved.source)

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

    def test_can_update_source_column_values(self):
        f0 = Source()
        f0.source = "qwerty"
        f0.save()

        f1 = Source.objects.filter(source=f0.source).first()
        f1.source = "secondary"
        f1.save()

        f2 = Source.objects.filter(pk=f1.pk).first()
        self.assertEqual("Secondary", f2.source)

    def test_delete_Source_with_cc_raises_restricted_error(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.parent = parent
        f0.save()

        with self.assertRaises(RestrictedError):
            source.delete()


class FundCenterModelTest(TestCase):
    fc_1111AA = {"fundcenter": "1111aa", "shortname": "bedroom", "parent": None}

    def test_string_representation(self):
        obj = FundCenter(fundcenter="1234aa", shortname="abcdef", parent=None)
        self.assertEqual("1234AA - ABCDEF", str(obj))

    def test_verbose_name_plural(self):
        self.assertEqual("Fund Centers", str(FundCenter._meta.verbose_name_plural))

    def test_can_save_and_retrieve_fund_centers(self):
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.shortname = "defgth"
        first_fc.parent = None
        first_fc.full_clean()
        first_fc.save()

        saved_fc = FundCenter.objects.get(pk=first_fc.pk)
        self.assertEqual("1111AA", saved_fc.fundcenter)

    def test_saved_fund_center_as_uppercase(self):
        first_fc = FundCenter()
        first_fc.fundcenter = "1111aa"
        first_fc.shortname = "defgth"
        first_fc.parent = None
        first_fc.full_clean()
        first_fc.save()

        saved = FundCenter.objects.get(pk=first_fc.pk)
        self.assertEqual("1111AA", saved.fundcenter)
        self.assertEqual("DEFGTH", saved.shortname)

    def test_can_save_POST_request(self):
        data = {"fundcenter": "zzzz33", "shortname": "Kitchen FC", "parent": ""}
        response = self.client.post("/fundcenter/fundcenter-add/", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(FundCenter.objects.count(), 1)
        obj = FundCenter.objects.first()
        self.assertEqual(obj.fundcenter, "ZZZZ33")
        self.assertEqual(obj.shortname, "KITCHEN FC")

    # TODO
    # def test_can_delete_POST_request():
    #    pass

    def test_can_update_fund_center_column_values(self):
        f0 = FundCenter(**self.fc_1111AA)
        f0.save()

        f1 = FundCenter.objects.get(pk=f0.pk)
        f1.fundcenter = "0000ff"
        f1.save()

        f2 = FundCenter.objects.get(pk=f1.pk)
        self.assertEqual("0000FF", f2.fundcenter)

    def test_can_delete_fund_center(self):
        f0 = FundCenter(**self.fc_1111AA)
        f0.save()

        f1 = FundCenter.objects.get(pk=f0.id)
        f1.delete()

        self.assertEqual(0, Fund.objects.count())

    def test_set_parent_to_itself_not_allowed(self):
        fc1 = FundCenter()
        fc1.fundcenter = "1111aa"
        fc1.shortname = "defgth"
        fc1.parent = None
        fc1.full_clean()
        fc1.save()

        fc1.parent = fc1
        with self.assertRaises(IntegrityError):
            fc1.save()


class CostCenterModelTest(TestCase):
    def test_string_representation(self):
        obj = CostCenter(**CC_1234FF)
        self.assertEqual("1234FF - Food and drink", str(obj))

    def test_verbose_name_plural(self):
        self.assertEqual("Cost Centers", str(CostCenter._meta.verbose_name_plural))

    def test_can_save_and_retrieve_cost_centers(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        cc = CostCenter(**CC_1234FF)
        cc.fund = fund
        cc.source = source
        cc.parent = parent
        # cc.full_clean()
        cc.save()

        saved_cc = CostCenter.objects.cost_center(cc.costcenter)
        self.assertEqual(CC_1234FF["costcenter"].upper(), saved_cc.costcenter)

    def test_saved_cost_center_as_uppercase(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        cc = CostCenter(**CC_1234FF)
        cc.fund = fund
        cc.source = source
        cc.parent = parent
        cc.costcenter = "1111aa"
        cc.shortname = "should be uppercase"
        cc.full_clean()
        cc.save()

        saved = CostCenter.objects.cost_center(cc.costcenter)
        self.assertEqual(cc.costcenter.upper(), saved.costcenter)
        self.assertEqual(cc.shortname.upper(), saved.shortname)

    def test_can_save_POST_request(self):
        data = CC_1234FF.copy()
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        data["fund"] = fund.pk
        data["source"] = source.pk
        data["parent"] = parent.pk
        response = self.client.post("/costcenter/costcenter-add/", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CostCenter.objects.count(), 1)
        obj = CostCenter.objects.first()
        self.assertEqual(CC_1234FF["costcenter"].upper(), obj.costcenter)
        self.assertEqual(
            CC_1234FF["shortname"].upper(),
            obj.shortname,
        )

    def test_can_update_cost_center_column_values(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()

        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.parent = parent
        f0.save()
        f1 = CostCenter.objects.get(pk=f0.pk)
        f1.shortname = "new shortname"
        f1.save()

        f2 = CostCenter.objects.cost_center(f1.costcenter)
        self.assertEqual(f1.shortname.upper(), f2.shortname)

    def test_can_delete_cost_center(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        f0 = CostCenter(**CC_1234FF)
        f0.fund = fund
        f0.source = source
        f0.parent = parent
        f0.save()

        f1 = CostCenter.objects.cost_center(f0.costcenter)
        f1.delete()

        self.assertEqual(0, CostCenter.objects.count())

    def test_parent_cannot_be_cost_center(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()

        cc1 = CostCenter(**CC_1234FF)
        cc1.fund = fund
        cc1.source = source
        cc1.parent = parent
        cc1.save()

        cc2 = CostCenter(**CC_1234FF)
        cc2.costcenter = "1111aa"
        cc2.fund = fund
        cc2.source = source
        with self.assertRaises(ValueError):
            cc2.parent = cc1  # set a cost center as parent
            cc2.save()


class ForecastAdjustmentModelTest(TestCase):
    def test_string_representation(self):
        fund = Fund(fund="C113", name="NP", vote=1)
        cc = CostCenter(costcenter="8484WA", shortname="Kitchen", fund=fund)
        obj = ForecastAdjustment(costcenter=cc, fund=fund, amount=1000)
        self.assertEqual(str(obj), "8484WA - Kitchen - C113 - NP - 1000")

    def test_verbose_name_plural(self):
        self.assertEqual(str(ForecastAdjustment._meta.verbose_name_plural), "Forecast Adjustments")

    def test_can_save_and_retreive_forecast_adjustment(self):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        cc = CostCenter(**CC_1234FF)
        cc.fund = fund
        cc.source = source
        cc.parent = parent
        cc.full_clean()
        cc.save()

        fa = ForecastAdjustment()
        fa.costcenter = cc
        fa.fund = fund
        fa.amount = 1000
        fa.note = "Increase in demand"
        fa.save()

        f_saved = ForecastAdjustment.objects.get(pk=fa.pk)
        self.assertEqual(fa.amount, f_saved.amount)


class CostCenterAllocationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        fund = Fund(**FUND_C113)
        fund.save()
        source = Source(**SOURCE_1)
        source.save()
        parent = FundCenter(**FC_1111AA)
        parent.save()
        cc = CostCenter(**CC_1234FF)
        cc.fund = fund
        cc.source = source
        cc.parent = parent
        cc.full_clean()
        cc.save()
        cls.data = {
            "costcenter": cc,
            "fund": fund,
            "amount": 100,
            "fy": 2024,
            "quarter": "Q0",
        }

    def test_string_representation(self):
        allocation = CostCenterAllocation(**self.data)
        self.assertEqual(str(allocation), "1234FF - FOOD AND DRINK - C113 - National Procurement - 2024Q0 100")

    def test_verbose_name_plural(self):
        self.assertEqual(str(ForecastAdjustment._meta.verbose_name_plural), "Forecast Adjustments")

    def test_save_and_retreive_allocation(self):
        allocation = CostCenterAllocation(**self.data)

        allocation.save()

        saved = CostCenterAllocation.objects.get(id=1)
        self.assertEqual(100, saved.amount)

    def test_save_with_invalid_quarter(self):
        self.data["quarter"] = "Q5"
        allocation = CostCenterAllocation(**self.data)

        with self.assertRaises(InvalidOptionException):
            allocation.save()

    def test_save_with_negative_allocation(self):
        self.data["amount"] = -1000
        allocation = CostCenterAllocation(**self.data)

        with self.assertRaises(InvalidAllocationException):
            allocation.save()

    def test_save_with_invalid_year(self):
        self.data["fy"] = 2200
        allocation = CostCenterAllocation(**self.data)

        with self.assertRaises(InvalidFiscalYearException):
            allocation.save()

    def test_can_save_POST_request(self):
        fund = Fund.objects.first()
        cc = CostCenter.objects.first()
        self.data["fund"] = fund.id
        self.data["costcenter"] = cc.id
        response = self.client.post("/costcenter/allocation-add/", data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(CostCenter.objects.count(), 1)
        obj = CostCenterAllocation.objects.first()
        self.assertEqual(self.data["amount"], obj.amount)
