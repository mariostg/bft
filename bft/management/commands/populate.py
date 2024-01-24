import os
from django.core.management.base import BaseCommand, CommandError
from main.settings import BASE_DIR, DEBUG
import pandas as pd
import numpy as np
from costcenter.models import (
    Fund,
    FundManager,
    Source,
    CostCenter,
    CostCenterManager,
    FundCenter,
    FundCenterManager,
    FundCenterAllocation,
    CostCenterAllocation,
)
from charges.models import CostCenterChargeImport, CostCenterChargeMonthly
from lineitems.models import LineForecast, LineItem
from bft.models import BftStatus, BftStatusManager
from users.models import BftUser

from bft import finstructure, uploadprocessor


class Command(BaseCommand):
    """
    A class to be used only for development purposes.  It serves to fill in some funds, sources, fund centers and cost centers.  Values fed in the database should match what is expected from the data to be used when running uploadtocsv which also uses test encumbrance report data.
    """

    def handle(self, *args, **options):
        if DEBUG:
            LineForecast.objects.all().delete()
            LineItem.objects.all().delete()
            BftUser.objects.update(default_cc="", default_fc="")  # So we can delete FC and CC
            CostCenter.objects.all().delete()
            Source.objects.all().delete()
            Fund.objects.all().delete()
            FundCenter.objects.all().delete()
            BftStatus.objects.all().delete()
            CostCenterAllocation.objects.all().delete()
            FundCenterAllocation.objects.all().delete()
            CostCenterChargeMonthly.objects.all().delete()
            CostCenterChargeImport.objects.all().delete()
            self.set_bft_status()
            self.set_fund()
            self.set_source()
            self.set_fund_center()
            self.set_cost_center()
            self.set_cost_center_allocation()
            self.set_fund_center_allocation()
        else:
            print("This capability is only available when DEBUG is True")

    def set_fund(self):
        uploadprocessor.FundProcessor("test-data/funds.csv", None).main()

    def set_source(self):
        uploadprocessor.SourceProcessor("test-data/source.csv", None).main()

    def set_fund_center(self):
        uploadprocessor.FundCenterProcessor("test-data/fundcenters.csv", None).main()

    def set_cost_center(self):
        uploadprocessor.CostCenterProcessor("test-data/costcenters.csv", None).main()

    def set_bft_status(self):
        bs = BftStatus()
        bs.status = "FY"
        bs.value = 2023
        bs.save()
        bs = BftStatus()
        bs.status = "QUARTER"
        bs.value = "1"
        bs.save()
        bs = BftStatus()
        bs.status = "PERIOD"
        bs.value = "1"
        bs.save()
        print(f"Set FY to {BftStatusManager().fy()}")
        print(f"Set Quarter to {BftStatusManager().quarter()}")
        print(f"Set Period to {BftStatusManager().period()}")

    def set_fund_center_allocation(self):
        uploadprocessor.FundCenterAllocationProcessor(
            "test-data/fundcenter-allocations.csv", 2023, "1", None
        ).main()

    def set_cost_center_allocation(self):
        uploadprocessor.CostCenterAllocationProcessor(
            "test-data/costcenter-allocations.csv", 2023, "1", None
        ).main()
