import pytest
from django.db.utils import IntegrityError

from reports.models import CostCenterMonthly


@pytest.mark.django_db
class TestCostCenterMonthlyModel:
    m1 = {
        "fund": "C113",
        "costcenter": "8484WA",
        "source": "Army",
        "fy": "2023",
        "period": "1",
        "spent": 3000,
        "commitment": 1000,
        "pre_commitment": 200,
        "fund_reservation": 200,
        "balance": 5000,
        "working_plan": 4000,
    }
    duplicate = {
        "fund": "C113",
        "costcenter": "8484WA",
        "source": "Army",
        "fy": "2023",
        "period": "1",
        "spent": 3000,
        "commitment": 1000,
        "pre_commitment": 200,
        "fund_reservation": 200,
        "balance": 5000,
        "working_plan": 4000,
    }

    @pytest.fixture
    def setup(self):
        # Will probably need a Command.handle() or something later to
        # populate monthly data
        pass

    def test_insert_single_row(self):
        md = CostCenterMonthly(**self.m1)
        md.save()
        assert 1 == CostCenterMonthly.objects.count()

    def test_insert_duplicate_row(self):
        md = CostCenterMonthly(**self.m1)
        md.save()
        md = CostCenterMonthly(**self.duplicate)
        with pytest.raises(IntegrityError):
            md.save()
