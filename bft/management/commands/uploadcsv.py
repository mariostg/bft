import logging
import os

from django.core.management.base import BaseCommand, CommandError

from bft.models import LineForecastManager, LineItem, LineItemImport
from bft.uploadprocessor import LineItemProcessor
from main.settings import BASE_DIR

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
        LineItemImport.objects.all().delete()
        rawtextfile = options["encumbrancefile"]

        if os.path.exists(rawtextfile):
            logger.info("-- BFT Download starts")
            rawtextfile = os.path.realpath(rawtextfile)
            er = LineItemProcessor(rawtextfile, None)
            if er.main():
                logger.info("Encumbrance data saved as csv and import raw table filled")
                li = LineItem()
                li.import_lines()
                li.set_fund_center_integrity()
                li.set_doctype()
                LineForecastManager().set_encumbrance_history_record()
                # LineForecastManager().set_unforecasted_to_spent()
                LineForecastManager().set_underforecasted()
                LineForecastManager().set_overforecasted()
                logger.info("-- BFT dowload complete")
        else:
            logger.warning(f"{rawtextfile} not found")
