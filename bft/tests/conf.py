from django.test import SimpleTestCase
from bft.conf import YEAR_CHOICES, QUARTERS


class ConfTest(SimpleTestCase):
    def test_read_quarters(self):
        q = QUARTERS

        self.assertEqual(5, len(q))
        self.assertEqual("Q0", q[0][0])

    def test_read_years(self):
        y = YEAR_CHOICES

        self.assertEqual(8, len(y))
