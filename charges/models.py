from django.db import models
from django.db.models import Sum, Value
from bft.models import BftStatusManager
from datetime import datetime
import os
import csv
import pandas as pd
import numpy as np
import logging
from main.settings import UPLOADS

logger = logging.getLogger("uploadcsv")


class CostCenterChargeImport(models.Model):
    """This class defines the model that represents the DND Actual Listings, Cost Center Transaction Listing report.  Historically, we call it Charges against cost center.  Each line read from the
    report during the uploadcsv command must match this model.

    This table contains the charges for the current fiscal year only.  Its content is to be deleted when moving to a new FY.

    Here is a sample report with its header and ons single line:
    |Fund|Cost Ctr|Cost Elem.|RefDocNo  |AuxAcctAsmnt_1  |    ValCOArCur|DocTyp|Postg Date|Per|
    -------------------------------------------------------------------------------------------
    |L111|46722A  |1101      |7000008167|ORD 11189281    |     1,273.38-|RX    |2023.10.17|  7|
    """

    fund = models.CharField(max_length=4)
    costcenter = models.CharField(max_length=6)
    gl = models.CharField(max_length=5)
    ref_doc_no = models.CharField(max_length=10)
    aux_acct_asmnt = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    doc_type = models.CharField(max_length=2, null=True, blank=True)
    posting_date = models.DateField()
    period = models.CharField(max_length=2)
    fy = models.PositiveSmallIntegerField("Fiscal Year", default=0)


class CostCenterChargeMonthlyManager(models.Manager):
    def flush_current(self) -> int:
        """Delete from the database the charges against cost center for the current FY and Period as defined by the BftStatusManager"""
        fy = BftStatusManager().fy()
        period = BftStatusManager().period()
        res = CostCenterChargeMonthly.objects.filter(fy=fy, period=period).delete()
        return res[0]

    def flush_monthly(self, fy: int, period: str) -> int:
        """Delete from the database the charges against cost center for the given fy and period"""
        res = CostCenterChargeMonthly.objects.filter(fy=fy, period=period).delete()
        return res[0]

    def insert_current(self, fy, period):
        """Insert in the monthly cost center charges table lines taken from charges import.  Insert selection is executed based on the provided fy and period equals to or less than provided period.  This is to ensure there is a rollup of charges on a monthly basis.

        Returns:
            int: Number of lines inserted
        """
        current = (
            CostCenterChargeImport.objects.filter(fy=fy, period__lte=period)
            .values("costcenter", "fund", "fy")
            .annotate(amount=Sum("amount"), period=Value(period))
        )
        lines = CostCenterChargeMonthly.objects.bulk_create([CostCenterChargeMonthly(**c) for c in current])
        linecount = len(lines)
        logger.info(f"Inserted {linecount} in table cost_center_charge_monthly")
        return linecount


class CostCenterChargeMonthly(models.Model):
    """This class defines the model that represents the cost center charges summarized by fy and period."""

    fund = models.CharField(max_length=4)
    costcenter = models.CharField("Cost Center", max_length=6)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    period = models.CharField(max_length=2)
    fy = models.PositiveSmallIntegerField("Fiscal Year", default=0)

    objects = CostCenterChargeMonthlyManager()

    def __str__(self):
        return f"{self.fund} {self.costcenter} {self.amount} {self.fy} {self.period}"

    class Meta:
        verbose_name_plural = "Cost Center charges monthly"


class CostCenterChargeProcessor:
    """
    CostCenterChargeProcessor class processes the Charges against cost center report.  It
    creates a csv file and populate the table using EncumbranceImport class.

    Raises:
        ValueError: If no encumbrance file name is provided.
        FileNotFoundError: If the encumbrance file is not found
    """

    def __init__(self):
        self.csv_file = f"{UPLOADS}/charges.csv"
        self.fy = BftStatusManager().fy()

    def to_csv(self, source_file: str, period: str):
        """Process the raw DRMIS Cost Center Charges report and save it as a csv file.

        Args:
            source_file (str): Full path of the DRMIS report

        Raises:
            ValueError: If columm Period has values that are not the same or period passed as argument does not match period in data file
        """
        df = pd.read_csv(
            source_file,
            dtype={2: object, 3: object, 8: object},
            sep="|",
            header=3,
            usecols=list(range(1, 10)),
            skipfooter=1,
            skipinitialspace=True,
            index_col=False,
        )

        # flush empty lines
        df = df[df["Fund"].notnull()]

        # Strip white spaces
        for col in df.columns:
            try:
                df[col] = df[col].str.strip()
            except AttributeError:
                pass

        # format date
        df["Postg Date"] = pd.to_datetime(df["Postg Date"], format="%Y.%m.%d")

        # strip , character from  ValCOArCur
        df["ValCOArCur"] = df["ValCOArCur"].str.replace(",", "")

        # move negative sign forward
        df.loc[df["ValCOArCur"].str.endswith("-"), "ValCOArCur"] = "-" + df["ValCOArCur"].str.replace("-", "")

        # set FY
        df["fy"] = self.fy

        # Confirm we have one single period
        periods = df["Per"].to_numpy()
        all_same = (periods[0] == periods).all()
        if not all_same:
            raise ValueError("element values in periods are not all the same")

        # Confirm period passed to command line matches those of csv file
        if periods[0] != period:
            raise ValueError(f"Requested period {period} does not match the periods in the file")

        df.to_csv(self.csv_file, index=False)

    def csv2cost_center_charge_import_table(self, fy, period):
        """Process the csv file that contains cost center charges and upload them in the destination table.ß"""
        CostCenterChargeImport.objects.filter(fy=fy, period=period).delete()
        with open(self.csv_file) as file:
            next(file)  # skip the header row
            reader = csv.reader(file)
            for row in reader:
                charge_line = CostCenterChargeImport(
                    fund=row[0],
                    costcenter=row[1],
                    gl=row[2],
                    ref_doc_no=row[3],
                    aux_acct_asmnt=row[4],
                    amount=row[5],
                    doc_type=row[6],
                    posting_date=row[7],
                    period=row[8],
                    fy=row[9],
                )
                charge_line.save()

    def monthly_charges(self, fy, period) -> int:
        m = CostCenterChargeMonthlyManager()
        m.flush_monthly(fy, period)
        return m.insert_current(fy, period)
