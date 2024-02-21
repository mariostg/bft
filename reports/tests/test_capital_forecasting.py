import pytest
from bft.models import BftStatusManager
from bft.management.commands import populate
from reports import capitalforecasting


@pytest.mark.django_db
class TestCapitalForecasting:
    @pytest.fixture
    def populate(self):
        hnd = populate.Command()
        hnd.handle()

    def test_setparams_without_fy(self, populate):
        self.cf = capitalforecasting.CapitalReport("2184da", "c113", "C.999999")
        assert "C113" == self.cf.fund.fund
        assert "2184DA" == self.cf.fundcenter.fundcenter
        assert "C.999999" == self.cf.capital_project.project_no
        assert BftStatusManager().fy() == self.cf.fy

    def test_setparams_with_fy(self, populate):
        self.cf = capitalforecasting.CapitalReport("2184da", "c113", "C.999999", 2024)
        assert "C113" == self.cf.fund.fund
        assert "2184DA" == self.cf.fundcenter.fundcenter
        assert "C.999999" == self.cf.capital_project.project_no
        assert 2024 == self.cf.fy

    def test_setparams_with_fy_range(self, populate):
        self.cf = capitalforecasting.CapitalReport("2184da", "c113", "C.999999", [2020, 2023])
        assert "C113" == self.cf.fund.fund
        assert "2184DA" == self.cf.fundcenter.fundcenter
        assert "C.999999" == self.cf.capital_project.project_no
        assert [2020, 2023] == self.cf.fy

    def test_setparams_with_quarter(self, populate):
        self.cf = capitalforecasting.CapitalReport("2184da", "c113", "C.999999", [2020, 2023], 1)
        assert "C113" == self.cf.fund.fund
        assert "2184DA" == self.cf.fundcenter.fundcenter
        assert "C.999999" == self.cf.capital_project.project_no
        assert 1 == self.cf.quarter
        assert [2020, 2023] == self.cf.fy


@pytest.mark.django_db
class TestCapitalForecastingHistoricalOutlookReport:
    @pytest.fixture
    def setup(self):
        self.cf = capitalforecasting.HistoricalOutlookReport("2184da", "c113", "c.999999", 2021)

    def test_dataset(self, setup):
        print(self.cf.hor_dataset)
