import pytest
from lineitems.models import LineItem
from encumbrance.management.commands import populate, uploadcsv


@pytest.mark.django_db
class TestLineItemManager:
    # Line Items tests
    def test_line_item_dataframe_no_line_items(self):
        r = LineItem

        assert True == r.objects.line_item_dataframe().empty

    def test_line_item_dataframe(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        r = LineItem

        li = r.objects.line_item_dataframe()

        assert 0 < len(li)

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

        r = LineItem
        li = r.objects.forecast_dataframe()
        assert 1 == len(li)

    def test_line_item_detailed_empty(self):
        r = LineItem
        assert True == r.objects.line_item_detailed().empty

    def test_line_item_detailed(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")

        r = LineItem
        assert 0 < len(r.objects.line_item_detailed())
