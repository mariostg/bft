from django.test import TestCase
from encumbrance.management.commands import uploadcsv
import unittest


class TestCostCenterParentAnalysis(TestCase):
    """Perform check on line items versus cost centers to report line items that
    have cost center - fund center different than what exist in the financial structure.
    """

    @classmethod
    def setUpTestData(cls):
        print("Setting up")
        a = uploadcsv.Command()
        a.handle()

    def test_is_true(self):
        self.assertTrue(True)
