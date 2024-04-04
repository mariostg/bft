import pytest

from bft.management.commands import populate
from reports import capitalforecasting


@pytest.mark.django_db
class TestCapitalForecasting:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_setparams_with_fy(self, populate):
        self.cf = capitalforecasting.CapitalReport("c113", "C.999999", 2024)
        assert "C113" == self.cf.fund.fund
        assert "C.999999" == self.cf.capital_project.project_no
        assert 2024 == self.cf.fy


@pytest.mark.django_db
class TestCapitalForecastingHistoricalOutlookReport:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()


@pytest.mark.django_db
class TestCapitalForecastingFEARStatus:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_dataframe(self, populate):
        cf = capitalforecasting.FEARStatusReport(
            "c113",
            2021,
            "c.999999",
        )
        cf.dataframe()
        assert cf.df.size == 44
