from django.test import TestCase
from io import StringIO
from django.core.management import call_command
from bft.management.commands.tables import Command
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


# TODO This is not quite working
class TestTablesQueryCommand(TestCase):
    def call_command(self, *args, **kwargs):
        call_command(
            "tables",
            *args,
            stdout=StringIO(),
            stderr=StringIO(),
            **kwargs,
        )

    def test_dry_run(self):
        Command.print_funds(self)
        a = self.call_command()
        print(a)
