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
    """
    EncumbranceImport class defines the model that represents the DND cost
    center encumbrance report single line item.  Each line read from the
    encumbrance report during the uploadcsv command must match this model
    """

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
    predecessordocno = models.CharField(max_length=20, null=True, blank=True, default="")
    predecessorlineno = models.CharField(max_length=3, null=True, blank=True, default="")
    reference = models.CharField(max_length=16, null=True, blank=True, default="")
    gl = models.CharField(max_length=5)
    duedate = models.DateField(null=True, blank=True)
    vendor = models.CharField(max_length=50, null=True, blank=True)
    createdby = models.CharField(max_length=50, null=True, blank=True, default="")


class Encumbrance:
    """
    Encumbrance class process the DND Cost Center encumbrance report.  It
    creates a csv file and populate the table using EncumbranceImport class.

    Raises:
        ValueError: If no encumbrance file name is provided.
        FileNotFoundError: If the encumbrance file is not found
    """

    COLUMNS = 22  # Includes empty columns at beginning and end of row
    CSVFILE = os.path.join(BASE_DIR, "drmis_data/encumbrance.csv")
    DRMIS_DIR = os.path.join(BASE_DIR, "drmis_data")
    CSVFIELDS = "|docno|lineno|acctassno|spent|balance|workingplan|fundcenter|fund|costcenter|internalorder|doctype|enctype|linetext|predecessordocno|predecessorlineno|reference|gl|duedate|vendor|createdby|"

    def __init__(self, rawtextfile=None):
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        if rawtextfile == None:
            raise ValueError("No file name provided")
        filepath = os.path.join(self.DRMIS_DIR, rawtextfile)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{rawtextfile} was not found")

        self.rawtextfile = filepath

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
            "csv": 0,  # csv line count data resulting from parsing the report
            "column_count": 22,  # Expected number of columns un the DRMIS report
        }

    def find_fund_center(self, line: str) -> str | None:
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
            int: 0 if nothing found, line number otherwise.
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

    def line_to_csv(self, line: str) -> list | None:
        """
        Split a line from the encumbrance report in a list

        Args:
            line (str): A line from the encumbrance report

        Returns:
            list | None: The list that contains the element from the string
            containing the data from the line passed as argument.
        """
        csv = line.split("|")
        csv.pop()
        csv.pop(0)
        for i, e in enumerate(csv):
            csv[i] = e.strip()
        if len(csv) == 20:
            return csv
        else:
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

    def write_encumbrance_file_as_csv(self) -> int:
        """
        Transform the encumbrance report raw file into a more useful CSV file.
        """
        lineno = 0
        lines_written = 0
        with open(self.rawtextfile, encoding="windows-1252") as lines, open(self.CSVFILE, "w") as recorder:
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

        with open(self.CSVFILE, "rb") as f:
            lines_written = sum(1 for _ in f)

        if lines_written > 0:
            self.data["csv"] = lines_written
            return lines_written
        else:
            raise RuntimeError("CSV file has not been written.")

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

        EncumbranceImport.objects.all().delete()
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
        fund_import = set(self.csv_get_unique_funds())
        fund = set(Fund.objects.all().values_list("fund", flat=True))
        return fund_import.difference(fund)

    def missing_costcenters(self):
        cc_import = set(self.csv_get_unique_costcenters())
        cc = set(CostCenter.objects.all().values_list("costcenter", flat=True))
        return cc_import.difference(cc)

    def __set_data(self) -> bool:
        if not self.rawtextfile:
            raise ValueError("Encumbrance report not defined.")

        with open(self.rawtextfile, encoding="windows-1252") as lines:
            for line in lines:
                if self.data["fy"] == None:
                    self.find_base_fy(line)
                if self.data["fc"] == None:
                    self.find_fund_center(line)
                if self.data["layout"] == None:
                    self.find_layout(line)
                if line == "":
                    break
        return True

    def run_all(self) -> bool:
        if self.__set_data():
            print(f"Fiscal Year : {self.data['fy']}")
            print(f"Fund Center : {self.data['fc']}")
            print(f"Report Layout : {self.data['layout']}")

        if self.is_dnd_cost_center_report():
            print("We have a DND Cost center encumbrance report.")

        if self.find_header_line() > 0:
            print(f"Column headers found at line {self.data['lineno']}")

        if self.write_encumbrance_file_as_csv() > 0:
            print(f"{self.data['csv']} lines have been written to {self.CSVFILE}")
        ok = True

        missing_fund = self.missing_fund()
        if missing_fund:
            for f in missing_fund:
                print(f"Missing fund {f}")
            ok = False

        missing_cc = self.missing_costcenters()
        if missing_cc:
            for cc in missing_cc:
                print(f"Missing costcenter {cc}")
            ok = False

        if ok:
            self.csv2table()
            linecount = EncumbranceImport.objects.count()
            print(f"{linecount} lines have been written to Encumbrance import table")
        else:
            print("Download did not complete.")
        return ok
