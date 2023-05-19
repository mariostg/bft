import os
from django.core.management.base import BaseCommand, CommandError
from main.settings import BASE_DIR, DEBUG

from costcenter.models import Fund, Source, CostCenter, FundCenter


class Command(BaseCommand):
    """
    A class to be used only for development purposes.  It serves to fill in some funds, sources, fund centers and cost centers.  Values fed in the database should match what is expected from the data to be used when running uploadtocsv which also uses test encumbrance report data.
    """

    def handle(self, *args, **options):
        if DEBUG:
            self.set_fund()
            self.set_source()
            self.set_fund_center()
        else:
            print("This capability is only available when DEBUG is True")

    def set_fund(self):
        items = [
            {"fund": "C113", "name": "National Procurement", "vote": "1"},
            {"fund": "C116", "name": "Kitchen Procurement", "vote": "5"},
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
        items = [
            {"fundcenter": "1111AB", "shortname": "bedroom", "parent": None},
        ]
        for item in items:
            try:
                found = FundCenter.objects.get(fundcenter=item["fundcenter"])
                if found:
                    print(f"Fund Center {found} exists")
            except FundCenter.DoesNotExist:
                new_item = FundCenter.objects.create(**item)
                print(f"Created Fund Center {new_item}")
