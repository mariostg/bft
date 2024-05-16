from django.core.management.base import BaseCommand

from bft.conf import PERIODKEYS
from bft.models import BftStatus, CostCenterManager, FundManager
from reports.utils import CostCenterMonthlyPlanReport


class Command(BaseCommand):
    """A management command class to handle the update of monthly allocation."""

    help = "Update and show monthly allocation."

    def add_arguments(self, parser):
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
            "--costcenter",
            action="store",
            help="Use this Cost Center for reporting and updating data",
        )
        parser.add_argument(
            "--fund",
            action="store",
            help="Use this fund in report query.",
        )

    def handle(self, *args, fy, period, costcenter, fund, **options):
        if costcenter:
            costcenter = costcenter.upper()
            if not CostCenterManager().exists(costcenter):
                msg = f"Cost center [{costcenter}] not found"
                self.stdout.write(style_func=self.style.WARNING, msg=msg)
                exit(0)

        if fund:
            fund = fund.upper()
            if not FundManager().exists(fund):
                msg = f"Fund [{fund}] not found"
                self.stdout.write(style_func=self.style.WARNING, msg=msg)
                exit(0)

        if not fy:
            fy = BftStatus.current.fy()

        if period not in PERIODKEYS:
            msg = f"Period [{period}] not valid.  Must be one of {PERIODKEYS}"
            self.stdout.write(style_func=self.style.WARNING, msg=msg)
            exit(0)

        report = CostCenterMonthlyPlanReport(fy, period, costcenter, fund)

        title = f"Monthly Summary for Cost Center = {costcenter}, fund={fund}, FY={fy}, period={period}"
        dots = "=" * len(title)
        print(dots)
        print(title)
        print(dots)
        print(report.dataframe())
