from django.db import models, connection
from django.db.models import Q
import os
import sys
import locale
import operator
from datetime import datetime
from functools import reduce

import csv
import re
import pandas as pd

from main.settings import BASE_DIR
from costcenter.models import CostCenter, Fund


class EncumbranceImport(models.Model):
    docno = models.CharField(max_length=10)
    lineno = models.CharField(max_length=7)  # lineno : acctassno
    # acctassno = models.CharField(max_length=3, null=True, blank=True)
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fundcenter = models.CharField(max_length=6)
    fund = models.CharField(max_length=4)
    costcenter = models.CharField(max_length=6)
    internalorder = models.CharField(max_length=7, null=True, blank=True)
    doctype = models.CharField(max_length=2, null=True, blank=True)
    enctype = models.CharField(max_length=21)
    linetext = models.CharField(max_length=50, null=True, blank=True, default="")
    predecessordocno = models.CharField(
        max_length=20, null=True, blank=True, default=""
    )
    predecessorlineno = models.CharField(
        max_length=3, null=True, blank=True, default=""
    )
    reference = models.CharField(max_length=16, null=True, blank=True, default="")
    gl = models.CharField(max_length=5)
    duedate = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=50, null=True, blank=True)
    createdby = models.CharField(max_length=50, null=True, blank=True, default="")


class Encumbrance:
    COLUMNS = 22  # Includes empty columns at beginning and end of row
    CSVFILE = os.path.join(BASE_DIR, "drmis_data/encumbrance.csv")
    CSVFIELDS = "|docno|lineno|acctassno|spent|balance|workingplan|fundcenter|fund|costcenter|internalorder|doctype|enctype|linetext|predecessordocno|predecessorlineno|reference|gl|duedate|vendor|createdby|"

    def __init__(self, rawtextfile=None):
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        if rawtextfile and os.path.exists(rawtextfile):
            self.rawtextfile = rawtextfile
        else:
            self.rawtextfile = None

        self.hint = {
            "fy": "|Base Fiscal Year",
            "fund_center": "|Funds Center",
            "layout": "|Layout",
            "header": "|Document N|Line Numbe|",
            "report": "DND Cost Center Encumbrance Report",
        }
        self.data = {
            "fy": None,  # FY read on report header
            "layout": None,  # LAyout read on report header
            "fc": None,  # Fund center read on report header
            "header": [],  # Columns header values read on report
            "lineno": 0,  # Linenumber where first column header was found
            # "csv": None,  # csv data resulting from parsing the report
            "column_count": 22,  # Expected number of columns un the DRMIS report
        }

    def find_fund(self, line: str) -> str | None:
        """Verify if whether or not a line contains the fund_center as defined in self.hint['fund_center'].

        Args:
            line (string): The line to test.

        Returns:
            str | None: The fund center found in self.hint['fund_center'], none if not found.
        """
        self.data["fc"] = None
        if line.startswith(self.hint["fund_center"]):
            parts = line.split("|")
            if len(parts) == 4:
                self.data["fc"] = parts[2].strip()
        # print(f"{self.find_fund.__name__}:Found fund {self.data['fc']}")
        return self.data["fc"]

    def find_base_fy(self, line: str) -> str | None:
        """Verify if whether or not a line contains the base fiscal year as defined in self.hint['fy'].

        Args:
            line (str): The line to test.

        Returns:
            str | None: The base fiscal year found in self.hint['fy'], none if not found.
        """
        self.data["fy"] = None
        if line.startswith(self.hint["fy"]):
            parts = line.split("|")
            if len(parts) == 4:
                self.data["fy"] = parts[2].strip()
        # print(f"Foud FY {self.data['fy']}")
        return self.data["fy"]

    def find_layout(self, line: str) -> str | None:
        """Verify if whether or not a line contains the report layout as defined in self.hint['layout']

        Args:
            line (str): The line to test.

        Returns:
            str|None: The report layout found in self.hint['layout'], none if not found.
        """
        self.data["layout"] = None
        if line.startswith(self.hint["layout"]):
            parts = line.split("|")
            if len(parts) == 4:
                self.data["layout"] = parts[2].strip()
        # print(f"Foud layout {self.data['layout']}")
        return self.data["layout"]

    def clean_header(self, header: list) -> None:
        """Strips empty first and last column and strips all blanks in column elements

        Args:
            header (list): The column header list to clean
        """
        if header[-1] == "" or header[-1] == "\n":
            header.pop()
        if header[0] == "" or header[-1] == "\n":
            header.pop(0)
        for i, e in enumerate(header):
            e = e.strip()
            self.data["header"] += [e]
        print("cleaned header")

    def find_header_line(self) -> int:
        """Attemps to find the row that contains the column header based on self.hint['header']

        Returns:
            int: _description_
        """

        lineno = 0
        with open(self.rawtextfile, encoding="windows-1252") as lines:
            for line in lines:
                lineno += 1
                if line.startswith(self.hint["header"]):
                    parts = line.split("|")
                    if len(parts) == self.COLUMNS:
                        self.clean_header(parts)
                        self.data["lineno"] = lineno
                        break
        # print(f"Foud header line {self.data['lineno']}")
        return self.data["lineno"]

    def is_dnd_cost_center_report(self) -> bool:
        """Attempts to find the string that identifies a DND Cost Center Report

        Returns:
            bool: True if fount, False otherwise.
        """
        try:
            with open(self.rawtextfile, encoding="windows-1252") as lines:
                for line in lines:
                    if line.startswith(self.hint["report"]):
                        # print("Foud DND Cost center report")
                        return True
                    if line == "":
                        print("DID not find DND Cost center report")
                        return False
        except TypeError:
            print("File name is not of expected type")
        except FileNotFoundError:
            print("File name was not found")
        return False

    def line_to_csv(self, line):
        csv = line.split("|")
        csv.pop()
        csv.pop(0)
        for i, e in enumerate(csv):
            csv[i] = e.strip()
        if len(csv) == 20:
            return csv
        else:
            print(csv)
            return None

    def is_data_line(self, line: str) -> bool:
        """Check if a line of the encumbrance report can be considered a line of data.
        Aline of data must start with |, followed by 10 letters, numbers or spaces, followed
        by 10 spaces or digits, and followed by | character.

        Args:
            line (str): A line from the encumbrance report to test

        Returns:
            bool: True if line can be considered a line of data, false otherwise.
        """
        if line == "" or len(line) < 2:
            return False
        if len(line) > 0 and re.search("^\|[A-Z0-9 ]{10}\|[\s\d]{10}\|", line):
            return True

        return False

    def write_encumbrance_file_as_csv(self):
        lineno = 0
        skipped = 0
        with open(self.rawtextfile, encoding="windows-1252") as lines, open(
            self.CSVFILE, "w"
        ) as recorder:
            writer = csv.writer(recorder, quoting=csv.QUOTE_ALL)
            header = self.line_to_csv(self.CSVFIELDS)
            writer.writerow(header)
            for line in lines:
                lineno += 1
                if lineno < self.data["lineno"]:
                    continue
                if self.is_data_line(line):
                    data = self.line_to_csv(line)
                    if data:
                        writer.writerow(data)
                    else:
                        skipped += 1
                        print("Skipped lines:", skipped)
        if lineno > 0:
            print(f"{lineno} have been written to {self.rawtextfile}")
        else:
            print("CSV file has not been written.")

    def csv_get_unique_funds(self):
        df = pd.read_csv(self.CSVFILE, usecols=["fund"])
        return df["fund"].unique()

    def csv_get_unique_costcenters(self):
        df = pd.read_csv(self.CSVFILE, usecols=["costcenter"])
        return df["costcenter"].unique()

    def csv2table(self):
        def str2float(n):
            try:
                return locale.atof(n)
            except ValueError:
                print(f"Failed to convert '{n}' to float")
                sys.exit()

        def str2date(s):
            if s == "":
                return None
            try:
                d = datetime.strptime(s, "%Y.%m.%d")
                return d
            except ValueError as e:
                print(f"Failed to convert {s} as date")
                sys.exit()

        with open(self.CSVFILE) as file:
            next(file)  # skip the header row
            reader = csv.reader(file)
            for row in reader:
                lineitem = EncumbranceImport(
                    docno=row[0],
                    lineno=f"{row[1]}:{row[2] or 0}",
                    # acctassno=row[2],
                    spent=str2float(row[3]),
                    balance=str2float(row[4]),
                    workingplan=str2float(row[5]),
                    fundcenter=row[6],
                    fund=row[7],
                    costcenter=row[8],
                    internalorder=row[9],
                    doctype=row[10],
                    enctype=row[11],
                    linetext=row[12],
                    predecessordocno=row[13],
                    predecessorlineno=row[14],
                    reference=row[15],
                    gl=row[16],
                    duedate=str2date(row[17]),
                    vendor=row[18],
                    createdby=row[19],
                )
                lineitem.save()

    def missing_fund(self):
        # fund_import = set(EncumbranceImport.objects.all().values_list("fund", flat=True))
        fund_import = set(self.csv_get_unique_funds())
        fund = set(Fund.objects.all().values_list("fund", flat=True))
        return fund_import.difference(fund)

    def missing_costcenters(self):
        # cc_import = set(EncumbranceImport.objects.all().values_list("costcenter", flat=True))
        cc_import = set(self.csv_get_unique_costcenters())
        cc = set(CostCenter.objects.all().values_list("costcenter", flat=True))
        return cc_import.difference(cc)

    def run_all(self) -> bool:
        with open(self.rawtextfile, encoding="windows-1252") as lines:
            for line in lines:
                if self.find_base_fy(line):
                    self.data["fy"] = line.split("|")
                if self.find_fund(line):
                    self.data["fund"] = line.split("|")
                if self.find_layout(line):
                    self.data["layout"] = line.split("|")
                if line == "":
                    break

        self.is_dnd_cost_center_report()
        self.find_header_line()
        self.write_encumbrance_file_as_csv()
        missing_fund = self.missing_fund()
        if missing_fund:
            print("There are missing funds:")
            for f in missing_fund:
                print(f)
            print("Operation aborted.")
            return False
        missing_cc = self.missing_costcenters()
        if missing_cc:
            print("There are missing cost centers:")
            for cc in missing_cc:
                print(cc)
            print("Operation aborted.")
            return False
        self.csv2table()

        return True
