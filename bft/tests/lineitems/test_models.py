import os

import pytest
from django.db.models import Sum
from django.test import TestCase

from bft.management.commands import populate
from bft.models import (CostCenterManager, LineForecast, LineForecastManager,
                        LineItem, LineItemImport)
from bft.uploadprocessor import LineItemProcessor
from main.settings import BASE_DIR


@pytest.mark.django_db
class TestLineItemManager:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()

    def test_get_line_items_when_cost_center_exists(self, setup, upload):
        li = LineItem.objects.cost_center("8484WA")
        assert li.count() > 0

    def test_get_line_items_when_cost_center_not_exists(self, setup):
        li = LineItem.objects.cost_center("0000C1")
        assert li is None


class TestLineItemModel:
    def test_string_representation(self):
        str_repr = LineItem(docno="4510XX45", lineno="45", enctype="Purchase Order")
        assert str(str_repr) == "Purchase Order 4510XX45-45"

    def test_verbose_name_plural(self):
        assert str(LineItem._meta.verbose_name_plural) == "Line Items"

    def test_number_of_fields(self):
        obj = LineItem()
        c = obj._meta.get_fields()
        assert 23 == len(c)


@pytest.mark.django_db
class TestLineItemImport:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()

    def test_insert_line_item_from_encumbrance_line(self, setup, upload):
        obj = LineItem()
        enc = LineItemImport.objects.first()
        retval = obj.insert_line_item(enc)

        assert 8 == retval

    def test_update_line_item_from_encumbrance_line(self, setup, upload):
        obj = LineItem()
        enc = LineItemImport.objects.first()
        retval = obj.insert_line_item(enc)

        enc.workingplan = enc.workingplan + 10000
        enc.spent = enc.spent + 10000
        enc.balance = enc.balance + 10000
        li = LineItem.objects.get(pk=retval)
        updated = obj.update_line_item(li, enc)

        assert enc.workingplan == updated.workingplan

    def test_update_line_item_bogus_cost_center(self, setup, upload):
        obj = LineItem()
        enc = LineItemImport.objects.first()
        retval = obj.insert_line_item(enc)

        li = LineItem.objects.get(pk=retval)
        enc.costcenter = "QQQQ33"

        updated = obj.update_line_item(li, enc)

        assert updated is None

    def test_line_items_have_orphans(self, setup, upload):
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
        assert ("999999", "123") in orphan
        assert isinstance(orphan, set)

    def test_line_items_no_orphans(self):
        # bring lines in
        li = LineItem()
        li.import_lines()

        # check it out
        orphan = li.get_orphan_lines()
        assert 0 == len(orphan)
        assert isinstance(orphan, set)

    def test_mark_line_orphan(self, setup, upload):
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
        assert 0 == li.workingplan
        assert 0 == li.spent
        assert 0 == li.balance
        assert "orphan" == li.status


class TestLineItemManagementTest:
    @pytest.fixture
    def setup():
        filldata = populate.Command()
        filldata.handle()

    def test_line_item_fund_center_wrong(self, setup, upload):
        # bring lines in and assign a bogus fund center
        li = LineItem()
        li.import_lines()
        li = LineItem.objects.first()
        li.fundcenter = "xxxx11"
        li.save()

        li.set_fund_center_integrity()
        assert 1 == LineItem.objects.filter(fcintegrity=False).count()


@pytest.mark.django_db
class TestLineForecastModel:
    @pytest.fixture
    def setup(self):
        hnd = populate.Command()
        hnd.handle()

    def test_create_forecast_higher_than_wp(self, setup, upload):
        li = LineItem.objects.all().first()
        fcst = LineForecast.objects.get(lineitem=li)

        fcst.forecastamount = li.workingplan + 10000
        fcst.save()

        fcst = LineForecastManager().get_line_forecast(li)
        assert fcst.forecastamount == li.workingplan

    def test_create_forecast_smaller_than_spent(self, setup, upload):
        li = LineItem.objects.filter(spent__gt=0).first()
        new_fcst = float(li.spent) * 0.1

        LineForecast.objects.filter(lineitem__pk=li.pk).update(
            forecastamount=new_fcst
        )

        fcst = LineForecastManager().get_line_forecast(li)
        assert fcst.forecastamount == new_fcst

    def test_forecast_document_number_to_working_plan(self, setup, upload):
        # each line item will have a forecast equivalent to its own working plan
        docno = "12663089"

        lf = LineForecast
        lines = LineItem.objects.filter(docno=docno)
        if not lines:
            raise AssertionError(f"No lines found in {docno}")
        target_forecast = lines.aggregate(Sum("workingplan"))["workingplan__sum"]
        lf().forecast_line_by_docno(docno, target_forecast)

        applied_forecast = LineItem.objects.filter(docno=docno).aggregate(
            Sum("fcst__forecastamount")
        )["fcst__forecastamount__sum"]
        assert applied_forecast == target_forecast

    def test_forecast_document_number_to_zero(self, setup, upload):
        # When setting document forecast to 0, forecast will consider spent and assign this value or 0.
        docno = "11111110"

        lf = LineForecast
        target_forecast = 0
        total_spent = LineItem.objects.filter(docno=docno).aggregate(Sum("spent"))[
            "spent__sum"
        ]
        lf().forecast_line_by_docno(docno, target_forecast)

        applied_forecast = LineItem.objects.filter(docno=docno).aggregate(
            Sum("fcst__forecastamount")
        )["fcst__forecastamount__sum"]
        assert total_spent is not None
        assert applied_forecast == total_spent

    def test_create_forecast_no_lines(self, setup):
        docno = "XXXX"
        lf = LineForecast()
        assert 0 == lf.forecast_line_by_docno(docno, 1000)

    @pytest.mark.parametrize(
        "docno, target_forecast",
        [
            ("12663089", 10000),  # "12663089" contains three lines with one having a spent of 5000
            ("11111110", 150000),  # "11111110" has one line only with a spent > 0
            ("12382523", 150000),  # "12382523" has one line, spent == 0
        ],
    )
    def test_forecast_line_by_docno(self, setup, upload, docno, target_forecast):
        LineForecast().forecast_line_by_docno(docno, target_forecast)

        forecast = LineForecast.objects.filter(lineitem__docno=docno).aggregate(Sum("forecastamount"))[
            "forecastamount__sum"
        ]

        assert target_forecast == forecast

    @pytest.mark.parametrize(
        "costcenter, target_forecast",
        [
            ("8484wa", 400000),
            ("8484wa", 300000),
        ],
    )
    def test_forecast_line_by_costcenter(self, setup, upload, costcenter, target_forecast):
        LineForecast().forecast_costcenter_lines(costcenter, target_forecast)

        costcenter = CostCenterManager().cost_center(costcenter)
        forecast = LineForecast.objects.filter(lineitem__costcenter=costcenter).aggregate(Sum("forecastamount"))[
            "forecastamount__sum"
        ]

        assert abs(target_forecast - forecast) <= 0.01


class TestLineItemImportStructure(TestCase):
    GOODFILE = os.path.join(BASE_DIR, "test-data/encumbrance_small.txt")
    WRONGFC = os.path.join(BASE_DIR, "test-data/encumbrance_wrong_fc.txt")
    WRONGFY = os.path.join(BASE_DIR, "test-data/encumbrance_wrong_fy.txt")
    WRONGLAYOUT = os.path.join(BASE_DIR, "test-data/encumbrance_wrong_layout.txt")

    @classmethod
    def setUpTestData(cls):
        cls.path = os.path.join(BASE_DIR, "test-data")

    def test_drmis_data_folder_exists(self):
        self.assertTrue(os.path.exists(self.path), "Test data directory not found")

    def test_exception_raised_if_no_file_provided(self):
        with self.assertRaises(ValueError):
            LineItemProcessor()

    def test_exception_raised_if_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            LineItemProcessor("Fakefile", None)

    def test_find_fund_center_line_good(self):
        er = LineItemProcessor(self.GOODFILE, None)
        fc = er.find_fund_center("Funds Center :     2184AA")
        self.assertEqual(fc, "2184AA")

    def test_find_fundcenter_line_bad(self):
        er = LineItemProcessor(self.WRONGFC, None)
        fc = er.find_fund_center("Funds Center        |2184AA |")
        self.assertNotEqual(fc, "2184AA")

    def test_find_fy_line_good(self):
        er = LineItemProcessor(self.GOODFILE, None)
        fy = er.find_base_fy("Base Fiscal Year :2023 ")
        self.assertEqual(fy, "2023")

    def test_find_fy_line_bad(self):
        er = LineItemProcessor(self.WRONGFY, None)
        fy = er.find_base_fy("Base Fiscal Year    |2023   |")
        self.assertNotEqual(fy, "2023")

    def test_is_dnd_cost_center_report(self):
        er = LineItemProcessor(self.GOODFILE, None)
        ok = er.is_dnd_cost_center_report()
        self.assertTrue(ok)

    def test_is_not_dnd_cost_center_report(self):
        fname = os.path.join(self.path, "encumbrance_errors.txt")
        er = LineItemProcessor(fname, None)
        ok = er.is_dnd_cost_center_report()
        self.assertFalse(ok)

    def test_clean_header(self):
        header = "|Document N|Line Numbe|AcctAssNo.| Cur Year s|    Cur YR Bal|    Total Cur.|Funds Cent|Fund|Cost Cente|Order       |Document T|Encumbrance Type     |Line Text                                         |Prd.doc.no|Pred doc.i|Reference       |G/L Accoun|Due date  |Vendor nam                         |Created by  |"
        header = header.split("|")
        er = LineItemProcessor(self.GOODFILE, None)
        er.clean_header(header)
        self.assertEqual(len(er.data["header"]), er.COLUMNS - 2)

    def test_find_header_line_returns_zero_on_failure(self):
        er = LineItemProcessor(os.path.join(self.path, "encumbrance_no_line_header.txt"), None)
        lineno = er.find_header_line()
        self.assertEqual(lineno, 0)

    def test_find_header_line_returns_non_zero_on_success(self):
        er = LineItemProcessor(self.GOODFILE, None)
        lineno = er.find_header_line()
        self.assertGreater(lineno, 0)

    def test_is_data_line(self):
        er = LineItemProcessor(self.GOODFILE, None)
        lines = [
            {"line": "|14518705  |       240|", "result": True},
            {"line": "|1451870511|       240|", "result": True},
            {"line": "|1451-8705 |       240|", "result": False},
            {"line": "|Docum     |       240|", "result": False},
            {"line": "Funds Center          ", "result": False},
        ]
        for line in lines:
            self.assertEqual(er.is_data_line(line["line"]), line["result"])

    def test_line_to_csv_returns_list_or_Exception(self):
        er = LineItemProcessor(self.GOODFILE, None)
        result_ok = er.line_to_csv(
            "|col1|col2|col3|col4|col5|col6|col7|col8|col9|col10|col11|col12|col13|col14|col15|col16|col17|col18|col19|col20|"
        )
        result_bad = "|col1|col2|col3|col4|col5|col6|col7|col8|col9|col10|col11|col12|col13|col14|col15|col16|col17|col18|col19|"

        self.assertEqual(20, len(result_ok), "List does not contain 20 elements")
        self.assertTrue(type(result_ok) is list, "Argument does not return a list")

        with pytest.raises(AttributeError):
            er.line_to_csv(result_bad)

    def test_run_all_stops_on_bad_cost_center_report(self):
        er = LineItemProcessor(self.GOODFILE, None)
        self.assertFalse(er.main())
