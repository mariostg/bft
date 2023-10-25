from django.core.management.base import BaseCommand
from charges.models import CostCenterChargeProcessor


class Command(BaseCommand):
    """
    Import DRMIS Cost Center Charges report into CostCenterChargeImport table and subsequently into Cost Center Monthly Data table.  drmis_datan folder must exist and contains reports as defined in test files for development purposes.
    """

    help = "Import Cost Center Charges into the system."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to_csv",
            action="store_true",
            help="Import DRMIS Report into CSV File",
        )
        parser.add_argument(
            "--to_table",
            action="store_true",
            help="Import DRMIS Report into import table",
        )

        parser.add_argument(
            "cc_charge_file",
            type=str,
            help="cc charge drmis report full path",
        )

    def handle(self, *args, to_csv, to_table, **options):
        cp = CostCenterChargeProcessor()
        csv_processed = False
        if to_csv:
            rawtextfile = options["cc_charge_file"]
            print(f"Send to csv using {rawtextfile}")
            cp.to_csv(rawtextfile)
            csv_processed = True
        if to_table and csv_processed:
            cp.csv2cost_center_charge_import_table()
