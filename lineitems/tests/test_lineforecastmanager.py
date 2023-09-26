import pytest
from bft.management.commands import populate, uploadcsv
from lineitems.models import LineForecastManager


@pytest.mark.django_db
class TestLineForecastManager:
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

        li_df = LineForecastManager().forecast_dataframe()
        assert True == ("Lineforecast_ID" in li_df.columns)
        assert True == ("Forecast" in li_df.columns)
        assert True == ("Delivery Date" in li_df.columns)
        assert 1 == len(li_df)
