import pytest
from charges.models import CostCenterChargeProcessor
import os


class TestChargeProcessor:
    @pytest.fixture
    def setup(self):
        self.test_file = "drmis_data/charges_cc_test.txt"
        self.csv_file = "drmis_data/charges.csv"

    def test_to_csv(self, setup):
        if os.path.exists(self.csv_file):
            os.remove(self.csv_file)
        cp = CostCenterChargeProcessor()
        cp.to_csv(self.test_file)

        with open(self.csv_file, "r") as f:
            line_count = f.readlines()

        assert 99 == len(line_count)
