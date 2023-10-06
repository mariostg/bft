import os
from django.core.management.base import BaseCommand, CommandError
from main.settings import BASE_DIR, DEBUG

from costcenter.models import (
    Fund,
    FundManager,
    Source,
    CostCenter,
    FundCenter,
    FundCenterManager,
    FundCenterAllocation,
    FinancialStructureManager,
    CostCenterAllocation,
)
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
            self.set_fund()
            self.set_source()
            self.set_fund_center()
            self.set_cost_center()
            self.set_bft_status()
            self.set_cost_center_allocation()
            self.set_fund_center_allocation()
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
        def set_children(parent, children):
            for child_obj in children:
                try:
                    found = FundCenter.objects.get(fundcenter=child_obj["fundcenter"])
                    if found:
                        print(f"Fund Center {found} exists")
                except FundCenter.DoesNotExist:
                    new_item = FundCenter.objects.create(**child_obj, fundcenter_parent=parent)
                    print(f"Created Fund Center {new_item}, sequence {new_item.sequence}")

        # Create root DND
        dnd_obj = FundCenter.objects.create(**finstructure.dnd)
        print(f"Created Fund Center {dnd_obj}, sequence {dnd_obj.sequence}")
        dnd = FundCenter.objects.get(fundcenter="0162ND")
        set_children(dnd, finstructure.dnd_children)

        special_ops = FundCenter.objects.get(fundcenter="6399AA")
        set_children(special_ops, finstructure.special_ops_children)

        admmat = FundCenter.objects.get(fundcenter="0153ZZ")
        set_children(admmat, finstructure.admmat_children)

        dglepm = FundCenter.objects.get(fundcenter="2184AA")
        set_children(dglepm, finstructure.dglepm_children)

        wd = FundCenter.objects.get(fundcenter="1985BA")
        set_children(wd, finstructure.wd_fundcenters)

        dglepm_corp = FundCenter.objects.get(fundcenter="2184BB")
        set_children(dglepm_corp, finstructure.dglepm_corp_fundcenters)

        dsspm = FundCenter.objects.get(fundcenter="2184BC")
        set_children(dsspm, finstructure.dsspm_fundcenters)

        davpm = FundCenter.objects.get(fundcenter="2184BD")
        set_children(davpm, finstructure.davpm_children)

        dsvpm = FundCenter.objects.get(fundcenter="2184BE")
        set_children(dsvpm, finstructure.dsvpm_fundcenters)

        dleps = FundCenter.objects.get(fundcenter="2184BK")
        set_children(dleps, finstructure.dleps_fundcenters)

        daspm = FundCenter.objects.get(fundcenter="2184BP")
        set_children(daspm, finstructure.daspm_fundcenters)

        dlcspm = FundCenter.objects.get(fundcenter="2184BQ")
        set_children(dlcspm, finstructure.dlcspm_fundcenters)

        dcsem = FundCenter.objects.get(fundcenter="2184BR")
        set_children(dcsem, finstructure.dcsem_fundcenters)

        daeme = FundCenter.objects.get(fundcenter="2184DA")
        set_children(daeme, finstructure.daeme_fundcenters)

        qete = FundCenter.objects.get(fundcenter="2689BQ")
        set_children(qete, finstructure.qete_fundcenters)

        a82184 = FundCenter.objects.get(fundcenter="2184A8")
        set_children(a82184, finstructure.a82184_fundcenters)

        c22184 = FundCenter.objects.get(fundcenter="2184C2")
        set_children(c22184, finstructure.c22184_fundcenters)

        c32184 = FundCenter.objects.get(fundcenter="2184C3")
        set_children(c32184, finstructure.c32184_fundcenters)

        cs2184 = FundCenter.objects.get(fundcenter="2184CS")
        set_children(cs2184, finstructure.cs2184_fundcenters)

        e32184 = FundCenter.objects.get(fundcenter="2184E3")
        set_children(e32184, finstructure.e32184_fundcenters)

        q32184 = FundCenter.objects.get(fundcenter="2184Q3")
        set_children(q32184, finstructure.q32184_fundcenters)

        q42184 = FundCenter.objects.get(fundcenter="2184Q4")
        set_children(q42184, finstructure.q42184_fundcenters)

        r22184 = FundCenter.objects.get(fundcenter="2184R2")
        set_children(r22184, finstructure.r22184_fundcenters)

        r32184 = FundCenter.objects.get(fundcenter="2184R3")
        set_children(r32184, finstructure.r32184_fundcenters)

        r62184 = FundCenter.objects.get(fundcenter="2184R6")
        set_children(r62184, finstructure.r62184_fundcenters)

        # xxxx = FundCenter.objects.get(fundcenter="")
        # xxxx_fundcenters = [
        #     {"fundcenter": "", "shortname": "", "fundcenter_parent": xxxx},
        #     {"fundcenter": "", "shortname": "", "fundcenter_parent": xxxx},
        # ]

    def set_cost_center(self):
        fund = Fund.objects.get(fund="C113")
        source = Source.objects.get(source="Kitchen")
        a32184 = FundCenter.objects.get(fundcenter="2184A3")
        FSM = FinancialStructureManager()
        items = [
            {
                "costcenter": "8484WA",
                "shortname": "Utensils",
                "fund": fund,
                "source": source,
                "isforecastable": True,
                "isupdatable": True,
                "note": "",
                "costcenter_parent": a32184,
            },
            {
                "costcenter": "8484XA",
                "shortname": "Food and drink",
                "fund": fund,
                "source": source,
                "isforecastable": True,
                "isupdatable": True,
                "note": "A quick and short note for 1234FF",
                "costcenter_parent": a32184,
            },
            {
                "costcenter": "8484YA",
                "shortname": "Basement Stuff",
                "fund": fund,
                "source": source,
                "isforecastable": True,
                "isupdatable": True,
                "note": "",
                "costcenter_parent": a32184,
            },
        ]
        for item in items:
            try:
                found = CostCenter.objects.get(costcenter=item["costcenter"])
                if found:
                    print(f"Cost Center {found} exists")
            except CostCenter.DoesNotExist:
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

        a = FundCenterAllocation.objects.create(fundcenter=root_fc, amount=1000, fy=fy, quarter=quarter, fund=fund)
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
