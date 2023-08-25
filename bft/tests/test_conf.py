import pytest
from bft.conf import YEAR_CHOICES, QUARTERS, PERIODS, STATUS


class TestConf:
    def test_read_quarters(self):
        q = QUARTERS

        assert 5 == len(q)
        assert 0 == q[0][0]

    def test_read_years(self):
        y = YEAR_CHOICES

        assert 8 == len(y)

    def test_read_periods(self):
        p = PERIODS

        assert 14 == len(p)
        assert "P1" == p[0][1]
        assert "P14" == p[13][1]

    def test_read_status(self):
        expected = ("FY", "FY"), ("QUARTER", "QUARTER"), ("PERIOD", "PERIOD")
        assert set(expected) == set(STATUS)
