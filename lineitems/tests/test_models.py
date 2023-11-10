from django.test import TestCase
import pytest
from django.db.models import Sum
from lineitems.models import LineItem, LineForecast, LineForecastManager
from encumbrance.models import EncumbranceImport, Encumbrance
from bft.management.commands import populate, uploadcsv


@pytest.mark.django_db
class TestLineItemManager:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_get_line_items_when_cost_center_exists(self, setup):
        li = LineItem.objects.cost_center("8484WA")
        assert li.count() > 0

    def test_get_line_items_when_cost_center_not_exists(self, setup):
        li = LineItem.objects.cost_center("0000C1")
        assert li == None


class LineItemModelTest(TestCase):
    def test_string_representation(self):
        str_repr = LineItem(docno="4510XX45", lineno="45", enctype="Purchase Order")
        self.assertEqual(str(str_repr), "Purchase Order 4510XX45-45")

    def test_verbose_name_plural(self):
        self.assertEqual(str(LineItem._meta.verbose_name_plural), "Line Items")

    def test_number_of_fields(self):
        obj = LineItem()
        c = obj._meta.get_fields()
        self.assertEqual(23, len(c))


class LineItemImportTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        filldata = populate.Command()
        filldata.handle()
        runner = Encumbrance("encumbrance_2184a3.txt")
        runner.run_all()

    def test_insert_line_item_from_encumbrance_line(self):
        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        self.assertEqual(1, retval)

    def test_update_line_item_from_encumbrance_line(self):
        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        enc.workingplan = enc.workingplan + 10000
        enc.spent = enc.spent + 10000
        enc.balance = enc.balance + 10000
        li = LineItem.objects.get(pk=retval)
        updated = obj.update_line_item(li, enc)

        self.assertEqual(enc.workingplan, updated.workingplan)

    def test_update_line_item_bogus_cost_center(self):
        obj = LineItem()
        enc = EncumbranceImport.objects.first()
        retval = obj.insert_line_item(enc)

        li = LineItem.objects.get(pk=retval)
        enc.costcenter = "QQQQ33"

        updated = obj.update_line_item(li, enc)

        self.assertEqual(None, updated)

    def test_line_items_have_orphans(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        # alter a line to make it orphan
        li = LineItem.objects.first()
        li.docno = "999999"  # To make it orphan.
        li.lineno = "123"
        li.save()

        # check it out
        orphan = li.get_orphan_lines()
        self.assertIn(("999999", "123"), orphan)
        self.assertIsInstance(orphan, set)

    def test_line_items_no_orphans(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        # check it out
        orphan = li.get_orphan_lines()
        self.assertEqual(0, len(orphan))
        self.assertIsInstance(orphan, set)

    def test_mark_line_orphan(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        li = LineItem.objects.first()
        li.docno = "999999"  # To make it orphan.
        li.lineno = "123"
        li.save()

        orphan = li.get_orphan_lines()
        li.mark_orphan_lines(orphan)
        li = LineItem.objects.get(docno="999999", lineno="123")
        self.assertEqual(0, li.workingplan)
        self.assertEqual(0, li.spent)
        self.assertEqual(0, li.balance)
        self.assertEqual("orphan", li.status)


class LineItemManagementTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        filldata = populate.Command()
        filldata.handle()
        runner = Encumbrance("encumbrance_2184a3.txt")
        runner.run_all()

    def test_line_item_fund_center_wrong(self):
        # bring lines in and assign a bogus fund center
        li = LineItem()
        li.import_lines()
        li = LineItem.objects.first()
        li.fundcenter = "xxxx11"
        li.save()

        li.set_fund_center_integrity()
        self.assertEqual(1, LineItem.objects.filter(fcintegrity=False).count())


@pytest.mark.django_db
class TestLineForecastModel:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184A3.txt")

    def test_create_forecast(self, setup):
        li = LineItem.objects.all().first()
        new_fcst = li.workingplan - 10

        line_fcst = LineForecast()
        line_fcst.lineitem = li
        line_fcst.forecastamount = new_fcst
        line_fcst.save()

        fcst = LineForecastManager().get_line_forecast(li)
        assert fcst.forecastamount == new_fcst

    def test_create_forecast_higher_than_wp(self, setup):
        li = LineItem.objects.all().first()
        new_fcst = li.workingplan + 10000

        line_fcst = LineForecast()
        line_fcst.lineitem = li
        line_fcst.forecastamount = new_fcst
        line_fcst.save()

        fcst = LineForecastManager().get_line_forecast(li)
        assert fcst.forecastamount == li.workingplan

    def test_create_forecast_smaller_than_spent(self, setup):
        li = LineItem.objects.filter(spent__gt=0).first()
        new_fcst = float(li.spent) * 0.1

        line_fcst = LineForecast()
        line_fcst.lineitem = li
        line_fcst.forecastamount = new_fcst
        line_fcst.save()

        fcst = LineForecastManager().get_line_forecast(li)
        assert fcst.forecastamount == li.spent

    def test_forecast_document_number_to_working_plan(self, setup):
        # each line item will have a forecast equivalent to its own working plan
        docno = "12663089"

        lf = LineForecast
        lines = LineItem.objects.filter(docno=docno)
        if not lines:
            assert False, f"No lines found in {docno}"
        target_forecast = lines.aggregate(Sum("workingplan"))["workingplan__sum"]
        lf().forecast_line_by_line(docno, target_forecast)

        applied_forecast = lf.objects.aggregate(Sum("forecastamount"))["forecastamount__sum"]
        assert applied_forecast == target_forecast

    def test_forecast_document_number_to_zero(self):
        # When setting document forecast to 0, forecast will consider spent and assign this value or 0.
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")
        docno = "12699110"

        lf = LineForecast
        target_forecast = 0
        total_spent = LineItem.objects.filter(docno=docno).aggregate(Sum("spent"))["spent__sum"]
        lf().forecast_line_by_line(docno, target_forecast)

        applied_forecast = lf.objects.aggregate(Sum("forecastamount"))["forecastamount__sum"]
        assert applied_forecast == total_spent

    def test_create_forecast_no_lines(self, setup):
        docno = "XXXX"
        lf = LineForecast()
        assert 0 == lf.forecast_line_by_line(docno, 1000)
