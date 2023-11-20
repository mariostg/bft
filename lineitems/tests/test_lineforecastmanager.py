import pytest
from django.contrib.auth import get_user_model
from bft.management.commands import populate, uploadcsv
from lineitems.models import LineForecastManager, LineForecast, LineItem
from costcenter.models import CostCenter
from users.models import BftUser, BftUserManager


@pytest.mark.django_db
class TestLineForecastManager:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    @pytest.fixture
    def upload(self):
        up = uploadcsv.Command()
        up.handle(encumbrancefile="drmis_data/encumbrance_2184a3.txt")

    def test_line_forecast_dataframe(self, populate, upload):
        li = LineItem.objects.all().first()
        data = {"forecastamount": 1000, "lineitem": li}
        fcst = LineForecast(**data)
        fcst.save()

        li_df = LineForecastManager().forecast_dataframe()
        assert True == ("Lineforecast_ID" in li_df.columns)
        assert True == ("Forecast" in li_df.columns)
        assert True == ("Delivery Date" in li_df.columns)
        assert 3 == len(li_df)  # one line forecasted + 2 lines have spent.
        assert "int" == li_df.dtypes.Forecast

    def test_get_line_forecast_from_lineitem_when_no_forecast(self, populate, upload):
        lineitem = LineItem.objects.all().first()
        assert LineForecastManager().get_line_forecast(lineitem) == None

    def test_change_line_items_procurement_officer(self, populate, upload):
        mgr = LineForecastManager()
        costcenter = CostCenter.objects.get(costcenter="8484WA")
        li = LineItem.objects.filter(costcenter=costcenter).first()
        new_fcst = li.workingplan - 10
        line_fcst = LineForecast()
        line_fcst.lineitem = li
        line_fcst.forecastamount = new_fcst
        line_fcst.save()

        user = get_user_model()
        new_owner = user.objects.create_user(email="luigi@forces.gc.ca", password="foo")
        affected = mgr.update_owner(costcenter, new_owner)
        li = LineForecast.objects.filter(owner=new_owner).first()

        assert li.owner.username == "luigi"
        assert 3 == affected  # one line forecasted + 2 lines have spent.
