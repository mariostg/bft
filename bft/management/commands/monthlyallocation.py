from django.core.management.base import BaseCommand

from bft.conf import PERIODKEYS
from bft.management.commands._private import UserInput
from bft.models import BftStatus, CostCenter, CostCenterManager
from reports.utils import CostCenterMonthlyAllocationReport


class Command(BaseCommand):
    """A management command class to handle the update of monthly allocation."""

    help = "Update and show monthly allocation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update monthly allocation for current period and fy",
        )

        parser.add_argument(
            "--fy",
            action="store",
            help="Use this FY for reporting and updating data.  For viewing, if fy is not provided, use current FY",
        )
        parser.add_argument(
            "--period",
            action="store",
            help="Use this Period for reporting and updating data",
        )
        parser.add_argument(
            "--quarter",
            action="store",
            help="Use data from this quarter to populate for the given period.",
        )
        parser.add_argument(
            "--costcenter",
            action="store",
            help="Use this Cost Center for reporting and updating data",
        )
        parser.add_argument(
            "--fund",
            action="store",
            help="Use this fund in report query.",
        )

        parser.add_argument(
            "--view",
            action="store_true",
            help="Print dataframe of allocation data for given cost center, fund, fy and period",
        )

    def handle(self, *args, update, fy, period, view, costcenter, fund, quarter, **options):
        self.fund = fund
        self.fy = fy
        self.quarter = quarter
        if view:
            self.show_monthly(fy, period, costcenter, fund)
        if not update:
            self.stdout.write("No action to perform.")
        else:
            if period in PERIODKEYS:
                self.run_update(fy, period, quarter)
            else:
                raise ValueError(f"Period [{period}] not valid.  Must be one of {PERIODKEYS}")

    def run_update(self, fy=None, period=None, quarter=None):
        fy = UserInput().set_fy(fy=fy)
        period = UserInput().set_period(period=period)
        if not fy or not period or not period:
            self.stdout.write(style_func=self.style.SUCCESS, msg="Operation cancelled")
            return

        print(f"UPDATING... for FY {fy} and period {period} using {quarter} as reference")
        c = CostCenterMonthlyAllocationReport(fy, period, quarter=quarter)
        c.insert_grouped_allocation(c.sum_allocation_cost_center())

    def show_monthly(self, fy, period, costcenter, fund):
        if costcenter:
            costcenter = costcenter.upper()
        if not CostCenterManager().exists(costcenter):
            raise CostCenter.DoesNotExist(f"Cost center [{costcenter}] not found")
        if not fy:
            fy = BftStatus.current.fy()
        if period not in PERIODKEYS:
            msg = f"Period [{period}] not valid.  Must be one of {PERIODKEYS}"
            self.stdout.write(style_func=self.style.WARNING, msg=msg)
            exit(0)

        r = CostCenterMonthlyAllocationReport(fy=fy, period=period, costcenter=costcenter, fund=fund)
        df = r.dataframe()
        title = f"Monthly Allocation for Cost Center = {costcenter}, fund={fund}, FY={fy}, period={period}"
        dots = "=" * len(title)
        print(dots)
        print(title)
        print(dots)
        print(df)
