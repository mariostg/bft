from django.core.management.base import BaseCommand, CommandError
import os
from costcenter.models import Fund, CostCenter


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        # parser.add_argument("funds", nargs="+", type=str)

        # Named (optional) arguments
        parser.add_argument(
            "--table",
            action="store",
            help="List table content",
        )

    def handle(self, *args, **options):
        if options["table"] == "funds":
            self.print_funds()
        if options["table"] == "costcenter":
            self.print_costcenters()

    def print_funds(self):
        obj = Fund.objects.all()
        for elem in obj:
            print(f"{elem.fund}\t{elem.name}")

    def print_costcenters(self):
        obj = CostCenter.objects.all()
        for elem in obj:
            print(f"{elem.costcenter}\t{elem.name}")
