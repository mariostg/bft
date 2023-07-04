from django.test import TestCase
from reports.utils import Report
from bft.exceptions import LineItemsDoNotExistError
from encumbrance.management.commands import populate, uploadcsv


class TestReports(TestCase):
    def test_line_item_dataframe_no_line_items(self):
        r = Report()
        with self.assertRaises(LineItemsDoNotExistError):
            li = r.line_item_dataframe()

    def test_line_item_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        r = Report()

        li = r.line_item_dataframe()

        self.assertEqual(7, len(li))

    def test_line_forecast_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        from lineitems.models import LineForecast, LineItem

        li = LineItem.objects.all().first()
        data = {"forecastamount": 1000, "lineitem": li}
        fcst = LineForecast(**data)
        fcst.save()

        r = Report()
        li = r.forecast_dataframe()
        self.assertEqual(1, len(li))
