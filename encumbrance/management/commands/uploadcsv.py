from django.core.management.base import BaseCommand, CommandError
import os
from encumbrance.models import Encumbrance, EncumbranceImport
from lineitems.models import LineItem
from main.settings import BASE_DIR


class Command(BaseCommand):
    """Import CSV Encumbrance report into Line item table.  encumbrance/drmis_data
    must exist and contains encumbrance reports as defined in test files for development purposes.
    """

    help = "Import CSV Encumbrance report into Line item table."

    def add_arguments(self, parser):
        parser.add_argument(
            "encumbrance-file",
            type=str,
            help="Encumbrance report full path",
        )

    def handle(self, *args, **options):
        EncumbranceImport.objects.all().delete()
        rawtextfile = options["encumbrance-file"]

        if os.path.exists(rawtextfile):
            rawtextfile = os.path.realpath(rawtextfile)
            er = Encumbrance(rawtextfile)
            if er.run_all():
                self.stdout.write("Encumbrance data has saved as csv and import raw table filled")
                li = LineItem()
                li.import_lines()
                li.set_fund_center_integrity()
                li.display_import_progress()
        else:
            self.stdout.write(f"{rawtextfile} not found")
