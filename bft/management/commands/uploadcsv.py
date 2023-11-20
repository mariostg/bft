from django.core.management.base import BaseCommand, CommandError
import os
from encumbrance.models import Encumbrance, EncumbranceImport
from lineitems.models import LineItem, LineForecastManager
from main.settings import BASE_DIR

import logging

logger = logging.getLogger("uploadcsv")


class Command(BaseCommand):
    """Import CSV Encumbrance report into Line item table.  encumbrance/drmis_data
    must exist and contains encumbrance reports as defined in test files for development purposes.
    """

    help = "Import CSV Encumbrance report into Line item table."

    def add_arguments(self, parser):
        parser.add_argument(
            "encumbrancefile",
            type=str,
            help="Encumbrance report full path",
        )

    def handle(self, *args, **options):
        EncumbranceImport.objects.all().delete()
        rawtextfile = options["encumbrancefile"]

        if os.path.exists(rawtextfile):
            logger.info("-- BFT Download starts")
            rawtextfile = os.path.realpath(rawtextfile)
            er = Encumbrance(rawtextfile)
            if er.run_all():
                logger.info("Encumbrance data saved as csv and import raw table filled")
                li = LineItem()
                li.import_lines()
                li.set_fund_center_integrity()
                li.set_doctype()
                LineForecastManager().set_unforecasted_to_spent()
                logger.info("-- BFT dowload complete")
        else:
            logger.warning(f"{rawtextfile} not found")
