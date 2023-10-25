from django.db import models
from bft.models import BftStatusManager
from datetime import datetime
import os
import csv
import pandas as pd
import numpy as np


class CostCenterChargeImport(models.Model):
    """This class defines the model that represents the DND Actual Listings, Cost Center Transaction Listing report.  Historically, we call it Charges against cost center.  Each line read from the
    report during the uploadcsv command must match this model.

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
    fy = models.PositiveSmallIntegerField("Fiscal Year", default=BftStatusManager().fy())


class CostCenterChargeProcessor:
    """
    CostCenterChargeProcessor class processes the Charges against cost center report.  It
    creates a csv file and populate the table using EncumbranceImport class.

    Raises:
        ValueError: If no encumbrance file name is provided.
        FileNotFoundError: If the encumbrance file is not found
    """

    def __init__(self):
        self.csv_file = "drmis_data/charges.csv"
        self.fy = BftStatusManager().fy()

    def to_csv(self, source_file: str):
        """Process the raw DRMIS Cost Center Charges report and save it as a csv file.

        Args:
            source_file (str): Full path of the DRMIS report

        Raises:
            ValueError: If columm Period has values that are not the same.
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

        print(df)
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
