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

    def handle(self, *args, **options):
        EncumbranceImport.objects.all().delete()

        test_files = {
            "tiny": "encumbrance_tiny.txt",
            "small": "encumbrance_small.txt",
            "large": "encumbrance_large.txt",
            "full": "encumbrance_P1a.txt",
        }

        rawtextfile = os.path.join(BASE_DIR, "drmis_data", test_files["small"])

        if os.path.exists(rawtextfile):
            er = Encumbrance(rawtextfile)
            if er.run_all():
                self.stdout.write(
                    "Encumbrance data has saved as csv and import raw table filled"
                )
                data = EncumbranceImport.objects.all()
                li = LineItems()
                li.import_lines(data)
        else:
            self.stdout.write(f"{rawtextfile} not found")
