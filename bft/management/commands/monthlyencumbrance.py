from django.core.management.base import BaseCommand

from bft.conf import PERIODKEYS
from bft.management.commands._private import UserInput
from bft.models import BftStatus, CostCenter, CostCenterManager
from reports.utils import CostCenterMonthlyEncumbranceReport


class Command(BaseCommand):
    """A class to handle the update of monthly data."""

    help = "Update the monthly data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update monthly data for current period and fy",
        )
        parser.add_argument(
            "--fy",
            action="store",
            help="Set fy to use for setting monthly data and report query",
        )
        parser.add_argument(
            "--period",
            action="store",
            help="Set period to use for setting monthly data and report query",
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
            help="Print dataframe of monthly data for given cost center, fund, fy and period",
        )

    def handle(self, *args, update, fy, period, view, costcenter, fund, **options):
        self.fund = fund
        self.fy = fy
        if view:
            self.show_monthly(fy, period, costcenter, fund)
            return
        if not update:
            self.stdout.write("No action to perform.")
        else:
            if period in PERIODKEYS:
                self.run_update(fy, period)
            else:
                raise ValueError(f"Period [{period}] not valid.  Must be one of {PERIODKEYS}")

    def run_update(self, fy=None, period=None):
        fy = UserInput().set_fy(fy=fy)
        period = UserInput().set_period(period=period)
        if not fy or not period:
            self.stdout.write(style_func=self.style.SUCCESS, msg="Operation cancelled")
            return

        print(f"UPDATING... for FY {fy} and period {period}")
        c = CostCenterMonthlyEncumbranceReport(fy, period)
        c.insert_line_items(c.sum_line_items())

    def show_monthly(self, fy, period, costcenter: str, fund: str):
        if costcenter:
            costcenter = costcenter.upper()
        if not CostCenterManager().exists(costcenter):
            raise CostCenter.DoesNotExist(f"Cost center [{costcenter}] not found")

        if period not in PERIODKEYS:
            raise ValueError(f"Period [{period}] not valid.  Must be one of {PERIODKEYS}")

        r = CostCenterMonthlyEncumbranceReport(fy=fy, period=period, costcenter=costcenter, fund=fund)
        df = r.dataframe()
        print(df)
