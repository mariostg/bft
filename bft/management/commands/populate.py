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

from bft import finstructure


class Command(BaseCommand):
    """
    A class to be used only for development purposes.  It serves to fill in some funds, sources, fund centers and cost centers.  Values fed in the database should match what is expected from the data to be used when running uploadtocsv which also uses test encumbrance report data.
    """

    def handle(self, *args, **options):
        if DEBUG:
            LineForecast.objects.all().delete()
            LineItem.objects.all().delete()
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
        items = [
            {"fund": "C113", "name": "National Procurement", "vote": "1"},
            {"fund": "C503", "name": "Fund C503", "vote": "5"},
            {"fund": "C116", "name": "Kitchen Procurement", "vote": "5"},
            {"fund": "C523", "name": "Basement Procurement", "vote": "1"},
            {"fund": "CXXX", "name": "Bedroom Procurement", "vote": "1"},
            {"fund": "L101", "name": "Attic Procurement", "vote": "1"},
        ]
        for item in items:
            try:
                found = Fund.objects.get(fund=item["fund"])
                if found:
                    print(f"Fund {found} exists")
            except Fund.DoesNotExist:
                new_item = Fund.objects.create(**item)
                print(f"Created fund {new_item}")

    def set_source(self):
        items = [
            {"source": "Kitchen"},
            {"source": "Army"},
            {"source": "O&M"},
            {"source": "Ammo"},
            {"source": "Capital Program"},
            {"source": "Common"},
            {"source": "Disposal"},
            {"source": "Unknown"},
        ]

        for item in items:
            try:
                found = Source.objects.get(source=item["source"])
                if found:
                    print(f"Source {found} exists")
            except Source.DoesNotExist:
                new_item = Source.objects.create(**item)
                print(f"Created Source {new_item}")

    def set_fund_center(self):
        df = pd.read_csv("drmis_data/fundcenters.csv", delimiter="\t")
        df = df.replace(np.nan, None)
        df["shortname"] = df["shortname"].apply(lambda x: x.strip())
        items = df.to_dict("records")
        for item in items:
            print("ITEM", item)
            found = FundCenterManager().fundcenter(item["fundcenter"])
            if found:
                print(f"Fund Center {found} exists")
            else:
                parent = item["fundcenter_parent"]
                if parent:
                    item["fundcenter_parent"] = FundCenterManager().fundcenter(item["fundcenter_parent"])
                new_item = FundCenter.objects.create(**item)
                print(f"Created Fund Center {new_item}")

    def set_cost_center(self):
        df = pd.read_csv("drmis_data/costcenters-test.csv", delimiter="\t")
        df.loc[df.isupdatable.eq(-1), "isupdatable"] = True
        df.loc[df.isupdatable.ne(True), "isupdatable"] = False
        df.loc[df.isforecastable.eq(-1), "isforecastable"] = True
        df.loc[df.isforecastable.ne(True), "isforecastable"] = False
        df.loc[df.fund.eq("----"), "fund"] = "L101"
        df["shortname"] = df["shortname"].apply(lambda x: x.strip())
        for f in df["fund"].unique():
            try:
                Fund.objects.get(fund=f)
            except Fund.DoesNotExist:
                print(f"Fund {f} not found.  Cannot set cost centers")
                exit()

        for f in df["costcenter_parent"].unique():
            try:
                FundCenter.objects.get(fundcenter=f)
            except FundCenter.DoesNotExist:
                print(f"Fund Center {f} not found.  Cannot set cost centers")
                exit()

        items = df.to_dict("records")
        for item in items:
            fund = item["fund"]
            source = item["source"]
            cc_parent = item["costcenter_parent"]
            item["fund"] = Fund.objects.fund(fund)
            item["source"] = Source.objects.source(source)
            item["costcenter_parent"] = FundCenterManager().fundcenter(cc_parent)
            found = CostCenterManager().cost_center(item["costcenter"])
            if found:
                print(f"Cost Center {found} exists")
            else:
                new_item = CostCenter.objects.create(**item)
                print(f"Created Cost Center {new_item}")

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
        root_fundcenter = "2184DA"
        fy = 2023
        quarter = "1"

        root_fc = FundCenterManager().fundcenter(root_fundcenter)
        fund = FundManager().fund("C113")

        a = FundCenterAllocation.objects.create(
            fundcenter=root_fc, amount=1000, fy=fy, quarter=quarter, fund=fund
        )
        print("Created Allocation", a)
        a = FundCenterAllocation.objects.create(
            fundcenter=FundCenterManager().fundcenter("2184A3"), amount=500, fy=fy, quarter=quarter, fund=fund
        )
        print("Created Allocation", a)

    def set_cost_center_allocation(self):
        fund = Fund.objects.fund("C113")

        cc = CostCenter.objects.cost_center("8484WA")
        a = CostCenterAllocation.objects.create(costcenter=cc, fund=fund, fy=2023, quarter="1", amount=1000)
        print("Created Allocation", a)

        cc = CostCenter.objects.cost_center("8484XA")
        a = CostCenterAllocation.objects.create(costcenter=cc, fund=fund, fy=2023, quarter="1", amount=250)
        print("Created Allocation", a)
