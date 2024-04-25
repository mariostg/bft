from django_rich.management import RichCommand
from rich.table import Table

from bft.models import CostCenter, Fund, Source


class Command(RichCommand):
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
        if options["table"] == "fund":
            self.print_funds()
        if options["table"] == "source":
            self.print_sources()
        if options["table"] == "costcenter":
            self.print_costcenters()

    def print_funds(self):
        obj = Fund.objects.all()
        table = Table(title="Recorded Funds")
        table.add_column("Fund", no_wrap=True)
        table.add_column("Description", no_wrap=True)
        for elem in obj:
            table.add_row(
                elem.fund,
                elem.name,
            )
        self.console.print(table)

    def print_costcenters(self):
        obj = CostCenter.objects.all()
        table = Table(title="Recorded Cost Centers")
        table.add_column("Cost Center", no_wrap=True)
        table.add_column("Description", no_wrap=True)
        table.add_column("Fund", no_wrap=True)
        table.add_column("Source", no_wrap=True)
        table.add_column("Parent", no_wrap=True)
        table.add_column("Forecastable", no_wrap=True)
        table.add_column("Updatable", no_wrap=True)
        for elem in obj:
            table.add_row(
                elem.costcenter,
                elem.shortname,
                elem.fund.fund,
                elem.source.source,
                elem.costcenter_parent.fundcenter,
                str(elem.isforecastable),
                str(elem.isupdatable),
            )
        self.console.print(table)

    def print_sources(self):
        obj = Source.objects.all()
        for elem in obj:
            print(f"{elem.source}")
