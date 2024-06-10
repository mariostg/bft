from django.core.management.base import BaseCommand

from bft.management.commands._private import UserInput
from bft.models import CostCenter, CostCenterManager
from reports.utils import CostCenterInYearEncumbranceReport


class Command(BaseCommand):
    """A class to handle the update of monthly data."""

    help = "Update the monthly data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update in-year data for current fy",
        )
        parser.add_argument(
            "--fy",
            action="store",
            help="Set fy to use for setting in-year data and report query",
        )
        parser.add_argument(
            "--costcenter",
            action="store",
            help="Use this cost center in report query.",
        )
        parser.add_argument(
            "--fund",
            action="store",
            help="Use this fund in report query.",
        )

        parser.add_argument(
            "--view",
            action="store_true",
            help="Print dataframe of monthly data for given cost center, fund, fy",
        )

    def handle(self, *args, update, fy, view, costcenter, fund, **options):
        self.fund = fund
        self.fy = fy
        if view:
            self.show_in_year(fy, costcenter, fund)
            return
        if not update:
            self.stdout.write("No action to perform.")
            return
        self.run_update(fy)

    def run_update(self, fy=None):
        fy = UserInput().set_fy(fy=fy)
        if not fy:
            self.stdout.write(style_func=self.style.SUCCESS, msg="Operation cancelled")
            return

        self.stdout.write(style_func=self.style.SUCCESS, msg=f"UPDATING... In year for FY {fy}")

        c = CostCenterInYearEncumbranceReport(fy)
        c.insert_line_items(c.sum_line_items())

    def show_in_year(self, fy, costcenter: str, fund: str):
        if costcenter:
            costcenter = costcenter.upper()
        if not CostCenterManager().exists(costcenter):
            raise CostCenter.DoesNotExist(f"Cost center [{costcenter}] not found")

        r = CostCenterInYearEncumbranceReport(fy=fy, costcenter=costcenter, fund=fund)
        df = r.dataframe()
        print(df)
