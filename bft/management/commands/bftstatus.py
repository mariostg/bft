from django.core.management.base import BaseCommand

from bft.conf import PERIODKEYS
from bft.management.commands._private import UserInput
from bft.models import BftStatus, CostCenter, CostCenterManager
from reports.utils import CostCenterMonthlyEncumbranceReport


class Command(BaseCommand):
    """A class to display BFT Status."""

    help = "Display BFT Status"

    def handle(self, *args, **options):
        s = BftStatus.current
        self.stdout.write(f"Current fiscal year  {s.fy()}")
        self.stdout.write(f"Current quarter      {s.quarter()}")
        self.stdout.write(f"Current period       {s.period()}")
        return
