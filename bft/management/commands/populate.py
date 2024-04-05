"""
An administration tool for development purposes.  It serves to fill in some funds, sources, fund centers and cost centers.  Values fed in the database should match what is expected from the data to be used when running uploadtocsv which also uses test encumbrance report data.

Typical usage:
    python manage.py populate

Populate command uses the data available from the test-data folder.  This folder contains all the CSV files necessary to upload basic financial structure and allocations.

!!! warning
    populate command is only available in DEBUG mode.  It will overwrite all existing data in the system.

"""
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from bft import uploadprocessor
from bft.models import (BftStatus, BftStatusManager, BftUser, CapitalInYear,
                        CapitalNewYear, CapitalProject, CapitalYearEnd,
                        CostCenter, CostCenterAllocation,
                        CostCenterChargeImport, CostCenterChargeMonthly, Fund,
                        FundCenter, FundCenterAllocation, LineForecast,
                        LineItem, Source)
from main.settings import DEBUG


class Command(BaseCommand):
    def handle(self, *args, **options):
        if DEBUG:
            LineForecast.objects.all().delete()
            LineItem.objects.all().delete()
            BftUser.objects.update(default_cc="", default_fc="")  # So we can delete FC and CC
            CostCenter.objects.all().delete()
            CapitalProject.objects.all().delete()
            CapitalNewYear.objects.all().delete()
            CapitalInYear.objects.all().delete()
            CapitalYearEnd.objects.all().delete()
            Source.objects.all().delete()
            Fund.objects.all().delete()
            FundCenter.objects.all().delete()
            BftStatus.objects.all().delete()
            CostCenterAllocation.objects.all().delete()
            FundCenterAllocation.objects.all().delete()
            CostCenterChargeMonthly.objects.all().delete()
            CostCenterChargeImport.objects.all().delete()
            self.set_bft_status()
            self.set_fund()
            self.set_source()
            self.set_fund_center()
            self.set_cost_center()
            self.set_capital_project()
            self.set_capital_in_year()
            self.set_capital_new_year()
            self.set_capital_year_end()
            self.set_cost_center_allocation()
            self.set_fund_center_allocation()
        else:
            raise CommandError("This capability is only available when DEBUG is True")

    def set_fund(self):
        """
        Populate the database with all funds contained in the csv file.
        This operation is required before uploading cost centers.
        """
        uploadprocessor.FundProcessor("test-data/funds.csv", None).main()

    def set_source(self):
        """
        Populate the database with all sources contained in the csv file.
        This operation is required before uploading cost centers.
        """
        uploadprocessor.SourceProcessor("test-data/source.csv", None).main()

    def set_fund_center(self):
        """Populate the database with all fund centers contained in the csv file.
        This operation is required before uploading cost centers.
        """
        uploadprocessor.FundCenterProcessor("test-data/fundcenters.csv", None).main()

    def set_cost_center(self):
        """Populate the database with all fund centers contained in the csv file.
        All funds, sources and fund centers the the cost centers relies on must be contained in the
        related csv file.
        """
        uploadprocessor.CostCenterProcessor("test-data/costcenters.csv", None).main()

    def set_capital_project(self):
        """Populate the database with all the capital projects contained in the csv file.
        All funds and fund centers that the capital projects relies on must be contained in the
        related csv file."""
        uploadprocessor.CapitalProjectProcessor("test-data/capital-projects.csv", None).main()

    def set_capital_new_year(self):
        uploadprocessor.CapitalProjectNewYearProcessor("test-data/capital_new_year.csv", None).main()

    def set_capital_in_year(self):
        uploadprocessor.CapitalProjectInYearProcessor("test-data/capital_in_year.csv", None).main()

    def set_capital_year_end(self):
        uploadprocessor.CapitalProjectYearEndProcessor("test-data/capital_year_end.csv", None).main()

    def set_bft_status(self):
        """
        Set the current fiscal year to 2023, quarter to 1 and period to 1.
        """
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
        """Populate the database with all fund center allocations containted in the csv file.
        File must have FY of 2023 and quarter to 1.  All fund centers and funds indicated in
        the file must exists in the database.
        """
        uploadprocessor.FundCenterAllocationProcessor(
            "test-data/fundcenter-allocations.csv", 2023, "1", None
        ).main()

    def set_cost_center_allocation(self):
        """Populate the database with all cost center allocations containted in the csv file.
        File must have FY of 2023 and quarter to 1.  All cost centers and funds indicated in
        the file must exists in the database.
        """
        uploadprocessor.CostCenterAllocationProcessor(
            "test-data/costcenter-allocations.csv", 2023, "1", None
        ).main()
