import pytest

from bft.models import CostCenter, Fund, FundCenter, Source


@pytest.mark.django_db
class TestCostCenterManager:
    @pytest.fixture
    def setup(self):
        fc = FundCenter.objects.create(fundcenter="2184QQ", fundcenter_parent=None)
        fund = Fund.objects.create(fund="C111", name="Big fund", vote=1, download=True)
        s = Source.objects.create(source="La source")
        obj = CostCenter.objects.create(
            costcenter="8486AA", fund=fund, costcenter_parent=fc, source=s
        )
        self.pk = obj.pk

    def test_get_by_costcenter(self, setup):
        obj = CostCenter.objects.cost_center("8486AA")
        assert "8486AA" == obj.costcenter

    def test_get_by_pk(self, setup):
        obj = CostCenter.objects.pk(self.pk)

        assert obj.pk == self.pk


@pytest.mark.django_db
class TestFundManager:
    @pytest.fixture
    def setup(self):
        obj = Fund.objects.create(fund="C111", name="Big fund", vote=1, download=True)
        self.pk = obj.pk

    def test_get_by_name(self, setup):
        obj = Fund.objects.fund("C111")
        assert "C111" == obj.fund

    def test_get_by_pk(self, setup):
        obj = Fund.objects.pk(self.pk)
        assert obj.pk == self.pk


@pytest.mark.django_db
class TestSourceManager:
    @pytest.fixture
    def setup(self):
        s = Source.objects.create(source="La source")
        self.pk = s.pk

    def test_get_by_name(self, setup):
        s = Source.objects.source("La source")

        assert "La source" == s.source

    def test_get_by_pk(self, setup):
        s = Source.objects.pk(self.pk)

        assert s.pk == self.pk
