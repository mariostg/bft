import pytest
from django.contrib.auth import get_user_model

from bft.models import CostCenter, LineForecast, LineForecastManager, LineItem


@pytest.mark.django_db
class TestLineForecastManager:

    def test_line_forecast_dataframe(self, populatedata, upload):
        li = LineItem.objects.all().first()

        fcst = LineForecast.objects.get(lineitem=li)
        fcst.forecastamount = 1000
        fcst.save()

        li_df = LineForecastManager().forecast_dataframe()
        assert True == ("Lineforecast_ID" in li_df.columns)
        assert True == ("Forecast" in li_df.columns)
        assert True == ("Delivery Date" in li_df.columns)
        assert "int" == li_df.dtypes.Forecast

    def test_change_line_items_procurement_officer(self, populatedata, upload):
        mgr = LineForecastManager()
        costcenter = CostCenter.objects.get(costcenter="8484WA")

        user = get_user_model()
        new_owner = user.objects.create_user(email="luigi@forces.gc.ca", password="foo")
        mgr.update_owner(costcenter, new_owner)
        li = LineForecast.objects.filter(owner=new_owner).first()

        assert li.owner.username == "luigi"
