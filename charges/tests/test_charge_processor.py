import pytest
from charges.models import CostCenterChargeProcessor, CostCenterChargeImport
import os


class TestChargeProcessor:
    @pytest.fixture
    def setup(self):
        self.test_file = "drmis_data/charges_cc_test.txt"

    def test_to_csv(self, setup):
        cp = CostCenterChargeProcessor()
        cp.to_csv(self.test_file)

        with open(cp.csv_file, "r") as f:
            line_count = f.readlines()

        assert 99 == len(line_count)

    @pytest.mark.django_db
    def test_csv2table(self, setup):
        cp = CostCenterChargeProcessor()
        cp.to_csv(self.test_file)
        cp.csv2table()

        assert 98 == CostCenterChargeImport.objects.count()
