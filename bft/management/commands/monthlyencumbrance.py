from django.core.management.base import BaseCommand

from bft.conf import PERIODKEYS
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
            "--bftstatus",
            action="store_true",
            help="Print current Fy, period and quarter",
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

    def handle(self, *args, update, bftstatus, fy, period, view, costcenter, fund, **options):
        self.fund = fund
        self.fy = fy
        if bftstatus:
            s = BftStatus.current
            self.stdout.write(f"Current fiscal year  {s.fy()}")
            self.stdout.write(f"Current quarter      {s.quarter()}")
            self.stdout.write(f"Current period       {s.period()}")
            return
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

    def _get_user_input(self, hint: str) -> bool:
        choice = input(f"Continue using {hint} ? [y/n] ")
        if not choice or choice in ("N", "n"):
            _continue = False
        if choice in ("Y", "y"):
            _continue = True
        return _continue

    def set_fy(self, fy=None) -> str | None:
        currentfy = BftStatus.current.fy()
        if not fy:
            msg = f"You did not specify a fiscal year. Current fiscal year [{currentfy}] will be used."
            self.stdout.write(style_func=self.style.WARNING, msg=msg)
            if self._get_user_input(currentfy):
                fy = currentfy
        else:
            if fy != currentfy:
                msg = f"You specified a FY different than current value.\nCurrent is {currentfy}.\nYou provided {fy}"
                self.stdout.write(style_func=self.style.WARNING, msg=msg)
                if not self._get_user_input(fy):
                    fy = None

        return fy

    def set_period(self, period=None) -> str | None:
        currentperiod = BftStatus.current.period()
        if not period:
            msg = f"You did not specify a period. Current period [{currentperiod}] will be used."
            self.stdout.write(style_func=self.style.WARNING, msg=msg)
            if self._get_user_input(currentperiod):
                period = currentperiod
        else:
            if period != currentperiod:
                msg = f"You specified a period different than current value.\nCurrent is {currentperiod}.\nYou provided {period}"
                self.stdout.write(style_func=self.style.WARNING, msg=msg)
                if not self._get_user_input(period):
                    period = None
        return period

    def run_update(self, fy=None, period=None):
        fy = self.set_fy(fy)
        period = self.set_period(period)
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
