import os
from django.core.management.base import BaseCommand, CommandError
from main.settings import BASE_DIR, DEBUG

from costcenter.models import (
    Fund,
    Source,
    CostCenter,
    FundCenter,
    FinancialStructureManager,
    CostCenterAllocation,
)
from lineitems.models import LineForecast, LineItem
from bft.models import BftStatus, BftStatusManager


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
            self.set_fund()
            self.set_source()
            self.set_fund_center()
            self.set_cost_center()
            self.set_bft_status()
            self.set_cost_center_allocation()
        else:
            print("This capability is only available when DEBUG is True")

    def set_fund(self):
        items = [
            {"fund": "C113", "name": "National Procurement", "vote": "1"},
            {"fund": "C116", "name": "Kitchen Procurement", "vote": "5"},
            {"fund": "C523", "name": "Basement Procurement", "vote": "1"},
            {"fund": "CXXX", "name": "Bedroom Procurement", "vote": "1"},
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
        items = [{"source": "Kitchen"}]

        for item in items:
            try:
                found = Source.objects.get(source=item["source"])
                if found:
                    print(f"Source {found} exists")
            except Source.DoesNotExist:
                new_item = Source.objects.create(**item)
                print(f"Created Source {new_item}")

    def set_fund_center(self):
        # Create root FC
        fc = {"fundcenter": "1111AA", "shortname": "root", "parent": None}
        new_item = FundCenter.objects.create(**fc)
        root = FundCenter.objects.filter(fundcenter="1111AA").first()
        print(f"Created Fund Center {root}, sequence {root.sequence}")

        root_children = [
            {"fundcenter": "1111AB", "shortname": "AB", "parent": root},
            {"fundcenter": "1111AC", "shortname": "AC", "parent": root},
        ]
        for item in root_children:
            try:
                found = FundCenter.objects.get(fundcenter=item["fundcenter"])
                if found:
                    print(f"Fund Center {found} exists")
            except FundCenter.DoesNotExist:
                item["sequence"] = FinancialStructureManager().set_parent(fundcenter_parent=root)
                new_item = FundCenter.objects.create(**item)
                print(f"Created Fund Center {new_item}, sequence {new_item.sequence}")

        ab = FundCenter.objects.filter(fundcenter="1111AB").first()
        ab_children = [
            {"fundcenter": "2222BA", "shortname": "BA", "parent": ab},
            {"fundcenter": "2222BB", "shortname": "BB", "parent": ab},
        ]
        for item in ab_children:
            try:
                found = FundCenter.objects.get(fundcenter=item["fundcenter"])
                if found:
                    print(f"Fund Center {found} exists")
            except FundCenter.DoesNotExist:
                item["sequence"] = FinancialStructureManager().set_parent(fundcenter_parent=ab)
                new_item = FundCenter.objects.create(**item)
                print(f"Created Fund Center {new_item}")

    def set_cost_center(self):
        fund = Fund.objects.get(fund="C113")
        source = Source.objects.get(source="Kitchen")
        ab = FundCenter.objects.get(fundcenter="1111AB")
        ac = FundCenter.objects.get(fundcenter="1111AC")
        FSM = FinancialStructureManager()
        items = [
            {
                "costcenter": "8486B1",
                "shortname": "Utensils",
                "fund": fund,
                "source": source,
                "isforecastable": True,
                "isupdatable": True,
                "note": "",
                "parent": ac,
            },
            {
                "costcenter": "8486C1",
                "shortname": "Food and drink",
                "fund": fund,
                "source": source,
                "isforecastable": True,
                "isupdatable": True,
                "note": "A quick and short note for 1234FF",
                "parent": ab,
            },
            {
                "costcenter": "8486C2",
                "shortname": "Basement Stuff",
                "fund": fund,
                "source": source,
                "isforecastable": True,
                "isupdatable": True,
                "note": "",
                "parent": ab,
            },
        ]
        for item in items:
            try:
                found = CostCenter.objects.get(costcenter=item["costcenter"])
                if found:
                    print(f"Cost Center {found} exists")
            except CostCenter.DoesNotExist:
                item["sequence"] = FSM.set_parent(item["parent"], item)
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

    def set_cost_center_allocation(self):
        fund = Fund.objects.fund("C113")
        cc = CostCenter.objects.cost_center("8486B1")
        a = CostCenterAllocation()
        a.costcenter = cc
        a.fund = fund
        a.fy = 2023
        a.quarter = "1"
        a.amount = 1000
        a.save()
