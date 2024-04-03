import pytest

from bft.models import (BftStatus, CostCenterChargeImport,
                        CostCenterChargeProcessor)


class TestChargeProcessor:
    @pytest.fixture
    def setup(self):
        self.test_file = "test-data/cc-charges.txt"
        self.test_file_many_periods = "test-data/cc-charges-many-periods.txt"
        bs = BftStatus()
        bs.status = "FY"
        bs.value = 2023
        bs.save()

    @pytest.mark.django_db  # needed to get BFT status
    def test_to_csv(self, setup):

        cp = CostCenterChargeProcessor()
        cp.to_csv(self.test_file, "1")

        with open(cp.csv_file, "r") as f:
            line_count = f.readlines()
        assert 2 == len(line_count)

        with open(cp.csv_file, "r") as f:
            line = f.readline()
            expected_header = "Fund,Cost Ctr,Cost Elem.,RefDocNo  ,AuxAcctAsmnt_1  ,ValCOArCur,DocTyp,Postg Date,Per,fy\n"
            assert expected_header == line
            line = f.readline()
            first_line = "L111,46722A,1101,7000008167,ORD 11189281,-1273.38,RX,2023-10-17,1,2023\n"
            assert first_line == line

    @pytest.mark.django_db  # needed to get BFT status
    def test_to_csv_invalid_period(self, setup):

        cp = CostCenterChargeProcessor()
        with pytest.raises(ValueError):
            cp.to_csv(self.test_file, "7")

    @pytest.mark.django_db  # needed to get BFT status
    def test_to_csv_many_period(self, setup):

        cp = CostCenterChargeProcessor()
        with pytest.raises(ValueError):
            cp.to_csv(self.test_file_many_periods, "1")

    @pytest.mark.django_db
    def test_csv2cost_center_charge_import_table(self, setup):
        cp = CostCenterChargeProcessor()
        cp.to_csv(self.test_file, "1")
        cp.csv2cost_center_charge_import_table(2023, 1)

        assert 1 == CostCenterChargeImport.objects.count()
