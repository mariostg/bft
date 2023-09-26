import pytest
from lineitems.models import LineItem, LineItemManager
from bft.management.commands import populate, uploadcsv


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

        df = LineItemManager().line_item_dataframe()
        assert 0 < len(df)
        assert "Lineitem_ID" in df.columns
        assert "Costcenter_ID" in df.columns

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

        li_df = LineItemManager().forecast_dataframe()
        assert True == ("Lineforecast_ID" in li_df.columns)
        assert True == ("Forecast" in li_df.columns)
        assert True == ("Delivery Date" in li_df.columns)
        assert 1 == len(li_df)

    def test_line_item_detailed_empty(self):
        r = LineItem
        assert True == r.objects.line_item_detailed_dataframe().empty

    def test_line_item_detailed(self):
        hnd = populate.Command()
        hnd.handle()
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_tiny.txt")
        li_df = LineItemManager().line_item_detailed_dataframe()
        for c in li_df.columns:
            print(c)
        assert "Lineitem_ID" in li_df.columns
        assert "Costcenter_ID" in li_df.columns
        assert "Cost Center" in li_df.columns
        assert "Fund Center" in li_df.columns
        assert "Costcenter_ID" in li_df.columns
        assert "Fundcenter_ID" in li_df.columns
        assert "Source_ID" in li_df.columns
        assert "Fund_ID" in li_df.columns
        assert "Forecast" in li_df.columns
        assert 0 < len(li_df)
