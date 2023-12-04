from abc import ABC, abstractmethod
import csv
import locale
import os
import re
import sys
from datetime import datetime
from django.contrib import messages
from users.models import BftUser
from django.db import models, IntegrityError
import logging
import pandas as pd
import numpy as np
from bft.conf import QUARTERKEYS
from main.settings import BASE_DIR
from costcenter.models import (
    CostCenter,
    CostCenterAllocation,
    CostCenterManager,
    Fund,
    FundCenter,
    FundCenterAllocation,
    FundCenterManager,
    FundManager,
    Source,
    SourceManager,
)
from lineitems.models import LineItemImport, LineItem, LineForecastManager

logger = logging.getLogger("uploadcsv")


class UploadProcessor(ABC):
    class Meta:
        abstract = True

    def __init__(self, filepath, user: BftUser) -> None:
        self.filepath = filepath
        self.user = user
        self.header = None

    def header_good(self) -> bool:
        with open(self.filepath, "r") as f:
            header = f.readline()
        return self.header == header

    def dataframe(self):
        return pd.read_csv(self.filepath).fillna("")

    def as_dict(self, df: pd.DataFrame) -> dict:
        return df.to_dict("records")

    @abstractmethod
    def main(self):
        pass


class AllocationProcessor(UploadProcessor):

    """AllocationProcess is a utility class that allows for uploading of allocation in the BFT."""

    class Meta:
        abstract = True

    def __init__(self, filepath, fy, quarter, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.fy = fy
        self.quarter = quarter

    def dataframe(self):
        return pd.read_csv(self.filepath).fillna("")

    def as_dict(self, df: pd.DataFrame) -> dict:
        return df.to_dict("records")

    def _check_fund(self, data: pd.Series):
        expected = np.array(Fund.objects.all().values_list("fund", flat=True))
        provided = data.str.upper().to_numpy()
        mask = np.isin(provided, expected, invert=True)
        if mask.any():
            msg = f"Fund(s) not found during check fund {provided[mask]}"
            logger.error(msg)
            raise ValueError(msg)
        else:
            logger.info("Funds check success.")

    def _check_fy(self, data: pd.Series):
        fys = data.to_numpy()
        unique = (fys[0] == fys).all()
        if not unique:
            logger.error(f"Error allocation upload by {self.user.username}, {self.fy}, {self.quarter}")
            raise ValueError("Fiscal year data are not all the same")
        elif int(fys[0]) != int(self.fy):
            logger.error(
                f"Error allocation upload by {self.user.username}, FY data does not match request ({fys[0]} does not match {self.fy})"
            )
            raise ValueError("FY request does not match dataset")
        else:
            logger.info(
                f"Validated FY match for allocation upload by {self.user.username}, {self.fy}, {self.quarter}"
            )

    def _check_quarter(self, data: pd.Series):
        """Make sure all quarter are unique.  Make sure the quarter is in QUARTERKEYS. Make sure the unique quarter in the uploaded file matches the form request.

        Args:
            data (pd.Series): Pandas Series of quarters to validate

        Raises:
            ValueError: Raised of quarter not in QUARTERKEYS.
            ValueError: Raised if quarters are not unique.
            ValueError: Raised if quarter does not match form request.
        """
        if self.quarter not in QUARTERKEYS:
            msg = f"Invalid quarter {self.quarter}, expected one of {QUARTERKEYS}. {self.user.username}"
            logger.error(msg)
            raise ValueError(msg)

        quarters = data.to_numpy()
        unique = (quarters[0] == quarters).all()
        if not unique:
            msg = f"Quarters not all matching. {self.user.username}, {self.fy}, {self.quarter}"
            logger.error(msg)
            raise ValueError(msg)
        elif int(quarters[0]) != int(self.quarter):
            msg = f"Error allocation upload by {self.user.username}, Quarter data does not match request ({quarters[0]} does not match {self.quarter})"
            logger.error(msg)
            raise ValueError(msg)
        else:
            logger.info(
                f"Validated Quarter match for allocation upload by {self.user.username}, {self.fy}, {self.quarter}"
            )

    def _check_amount(self, data: pd.Series):
        """Make sure all amounts are either int of float and that amounts are greater that zero

        Args:
            data (pd.Series): Pandas Series of amounts to validate.

        Raises:
            ValueError: If any amount is of invalid data type
            ValueError: If any amount is less that or equal to zero.
        """
        amount = data.to_numpy()
        if amount.dtype not in ["int64", "float64"]:
            msg = f"Allocation upload by {self.user.username}, allocation amount of invalid type"
            logger.error(msg)
            raise ValueError(msg)
        mask = amount <= 0
        if mask.any():
            too_small = amount[mask]
            msg = f"Allocation uploadby {self.user.username}, allocation amount of 0 or less found."
            if len(too_small) > 10:
                msg += f" First 10 are {too_small[0:9]}"
            else:
                msg += f" Values are {str(too_small)}"
            raise ValueError(msg)


class FundCenterAllocationProcessor(AllocationProcessor):
    def __init__(self, filepath, fy, quarter, user: BftUser):
        AllocationProcessor.__init__(self, filepath, fy, quarter, user)
        self.header = "fundcenter,fund,fy,quarter,amount,note\n"

    def _check_fund_center(self, data: pd.Series):
        expected = np.array(FundCenter.objects.all().values_list("fundcenter", flat=True))
        provided = data.str.upper().to_numpy()
        mask = np.isin(provided, expected, invert=True)
        if mask.any():
            msg = f"Fund centers not found during check fund centers {provided[mask]}"
            logger.error(msg)
            raise ValueError(msg)
        else:
            logger.info("Fund centers check success.")

    def main(self, request=None):
        if not self.header_good():
            msg = f"Fund center allocation upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        checks = [
            {"check": self._check_fund, "param": df["fund"]},
            {"check": self._check_fund_center, "param": df["fundcenter"]},
            {"check": self._check_fy, "param": df["fy"]},
            {"check": self._check_quarter, "param": df["quarter"]},
            {"check": self._check_amount, "param": df["amount"]},
        ]
        for item in checks:
            try:
                item["check"](item["param"])
            except ValueError as err:
                logger.warn(err)
                if request:
                    messages.error(request, err)
                return
        _dict = self.as_dict(df)
        for item in _dict:
            item["fund"] = FundManager().fund(item["fund"])
            item["fundcenter"] = FundCenterManager().fundcenter(item["fundcenter"])
            item["owner"] = self.user
            alloc = FundCenterAllocation(**item)
            try:
                alloc.save()
            except IntegrityError as err:
                msg = f"Saving fund center allocation {item} generates {err}"
                logger.warn(msg)
                if request:
                    messages.error(request, msg)


class CostCenterAllocationProcessor(AllocationProcessor):
    def __init__(self, filepath, fy, quarter, user: BftUser):
        AllocationProcessor.__init__(self, filepath, fy, quarter, user)
        self.header = "costcenter,fund,fy,quarter,amount,note\n"

    def _check_cost_center(self, data: pd.Series):
        expected = np.array(CostCenter.objects.all().values_list("costcenter", flat=True))
        provided = data.str.upper().to_numpy()
        mask = np.isin(provided, expected, invert=True)
        if mask.any():
            msg = f"Cost centers not found during check cost centers {provided[mask]}"
            logger.error(msg)
            raise ValueError(msg)
        else:
            logger.info("Cost centers check success.")

    def main(self, request=None):
        if not self.header_good():
            msg = f"Cost center allocation upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        checks = [
            {"check": self._check_fund, "param": df["fund"]},
            {"check": self._check_cost_center, "param": df["costcenter"]},
            {"check": self._check_fy, "param": df["fy"]},
            {"check": self._check_quarter, "param": df["quarter"]},
            {"check": self._check_amount, "param": df["amount"]},
        ]
        for item in checks:
            try:
                item["check"](item["param"])
            except ValueError as err:
                logger.warn(err)
                if request:
                    messages.error(request, err)
                return
        _dict = self.as_dict(df)
        for item in _dict:
            item["fund"] = FundManager().fund(item["fund"])
            item["costcenter"] = CostCenterManager().cost_center(item["costcenter"])
            item["owner"] = self.user
            alloc = CostCenterAllocation(**item)
            try:
                alloc.save()
            except IntegrityError as err:
                msg = f"Saving cost center allocation {item} generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)


class FundProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "fund,name,vote\n"

    def main(self, request=None):
        if not self.header_good():
            msg = f"Fund upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        _dict = self.as_dict(df)
        for item in _dict:
            fund = Fund(**item)
            try:
                fund.save()
            except IntegrityError as err:
                msg = f"Saving fund {item} generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)


class SourceProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "source\n"

    def main(self, request=None):
        if not self.header_good():
            msg = f"Source upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        _dict = self.as_dict(df)
        for item in _dict:
            source = Source(**item)
            try:
                source.save()
            except IntegrityError as err:
                msg = f"Saving source {item} generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)


class FundCenterProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "fundcenter_parent,fundcenter,shortname\n"

    def main(self, request=None):
        if not self.header_good():
            msg = f"Fund Centers upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        _dict = self.as_dict(df)
        for item in _dict:
            if item["fundcenter_parent"] == "":
                item["fundcenter_parent"] = None
            else:
                item["fundcenter_parent"] = FundCenterManager().fundcenter(item["fundcenter_parent"])
            item_obj = FundCenter(**item)
            try:
                item_obj.save()
            except IntegrityError as err:
                msg = f"Saving fund center {item}  generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)


class CostCenterProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "costcenter_parent,costcenter,shortname,isforecastable,isupdatable,source,fund\n"

    def main(self, request=None):
        if not self.header_good():
            msg = f"Cost Centers upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        _dict = self.as_dict(df)
        for item in _dict:
            item["costcenter_parent"] = FundCenterManager().fundcenter(item["costcenter_parent"])
            item["fund"] = FundManager().fund(item["fund"])
            item["source"] = SourceManager().source(item["source"])
            item_obj = CostCenter(**item)
            try:
                item_obj.save()
            except IntegrityError as err:
                msg = f"Saving cost center {item} generates {err}"
                logger.warn(msg)
                if request:
                    messages.error(request, msg)


class LineItemProcessor(UploadProcessor):
    """
    LineItemProcessor class process the DND Cost Center encumbrance report.  It
    creates a csv file and populate the table using LineItemImport class.

    Raises:
        ValueError: If no encumbrance file name is provided.
        FileNotFoundError: If the encumbrance file is not found
    """

    COLUMNS = 22  # Includes empty columns at beginning and end of row
    CSVFILE = os.path.join(BASE_DIR, "drmis_data/encumbrance.csv")
    DRMIS_DIR = os.path.join(BASE_DIR, "drmis_data")
    CSVFIELDS = "|docno|lineno|acctassno|spent|balance|workingplan|fundcenter|fund|costcenter|internalorder|doctype|enctype|linetext|predecessordocno|predecessorlineno|reference|gl|duedate|vendor|createdby|"

    def __init__(self, filepath, request=None):
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        if filepath == None:
            raise ValueError("No file name provided")
        filepath = os.path.join(self.DRMIS_DIR, filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"{filepath} was not found")
        self.filepath = filepath

        if request:
            self.user = request.user
            self.request = request
            self.fundcenter = request.POST.get("fundcenter").upper()
        else:
            self.user = "Unregistered User"
            self.request = None

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
                self.data["fc"] = parts[2].strip().upper()
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
        with open(self.filepath, encoding="windows-1252") as lines:
            for line in lines:
                lineno += 1
                if line.startswith(self.hint["header"]):
                    parts = line.split("|")
                    if len(parts) == self.COLUMNS:
                        self.clean_header(parts)
                        self.data["lineno"] = lineno
                        break
        if not self.data["lineno"]:
            msg = f"Line Items upload by {self.user}, Failed to find header line."
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
        return self.data["lineno"]

    def is_dnd_cost_center_report(self) -> bool:
        """Attempts to find the string that identifies a DND Cost Center Report

        Returns:
            bool: True if fount, False otherwise.
        """
        try:
            with open(self.filepath, encoding="windows-1252") as lines:
                for line in lines:
                    if line.startswith(self.hint["report"]):
                        logger.info("Found DND Cost Center report")
                        return True
                    if line == "\n":
                        logger.error("DID not find DND Cost center report.")
                        return False
        except TypeError:
            msg = "File name is not of expected type"
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
        except FileNotFoundError:
            msg = "File name was not found"
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
        logger.error("DID not find DND Cost center report.")
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
        with open(self.filepath, encoding="windows-1252") as lines, open(self.CSVFILE, "w") as recorder:
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

        LineItemImport.objects.all().delete()
        with open(self.CSVFILE) as file:
            next(file)  # skip the header row
            reader = csv.reader(file)
            for row in reader:
                lineitem = LineItemImport(
                    docno=row[0],
                    lineno=f"{row[1]}:{row[2] or 0}",
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
        missing_funds = fund_import.difference(fund)
        if missing_funds:
            msg = "There are missing funds", missing_funds
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
            return True

    def missing_costcenters(self):
        cc_import = set(self.csv_get_unique_costcenters())
        cc = set(CostCenter.objects.all().values_list("costcenter", flat=True))
        missing_cc = cc_import.difference(cc)
        if missing_cc:
            msg = "There are missing cost centers", missing_cc
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
            return True

    def _set_data(self) -> bool:
        if not self.filepath:
            raise ValueError("Encumbrance report not defined.")

        with open(self.filepath, encoding="windows-1252") as lines:
            is_set = [False, False, False]
            for line in lines:
                if self.data["fy"] == None:
                    is_set[0] = self.find_base_fy(line)
                if self.data["fc"] == None:
                    is_set[1] = self.find_fund_center(line)
                if self.data["layout"] == None:
                    is_set[2] = self.find_layout(line)
                if line == "":
                    break

            logger.info(f"Fiscal Year : {self.data['fy']}")
            logger.info(f"Fund Center : {self.data['fc']}")
            logger.info(f"Report Layout : {self.data['layout']}")
            if not all(is_set):
                msg = f"Line Items upload by {self.user}.  Could not find FY, FC or report Layout in report header."
                logger.error(msg)
                if self.request:
                    messages.error(self.request, msg)
        return all(is_set)

    def _fundcenter_matches_report(self):
        if not self.request:
            logger.error("http request not available")
            return False
        if self.fundcenter != self.data["fc"]:
            msg = f"{self.fundcenter} does not match report found in dataset: {self.data['fc']}"
            logger.error(msg)
            messages.error(self.request, msg)
            return False
        return True

    def main(self) -> bool:
        logger.info(f"Begin Upload processing by {self.user}")
        if not self._set_data():
            return False

        if not self._fundcenter_matches_report():
            return False

        if not self.is_dnd_cost_center_report():
            return False

        logger.info("We have a DND Cost center encumbrance report.")

        if self.find_header_line() == 0:
            return False

        if self.write_encumbrance_file_as_csv() == 0:
            return False

        if self.missing_fund():
            return False

        if self.missing_costcenters():
            return False

        self.csv2table()
        linecount = LineItemImport.objects.count()
        logger.info(f"{linecount} lines have been written to Encumbrance import table")

        li = LineItem()
        li.import_lines()
        li.set_fund_center_integrity()
        li.set_doctype()
        LineForecastManager().set_encumbrance_history_record()
        # LineForecastManager().set_unforecasted_to_spent()
        LineForecastManager().set_underforecasted()
        LineForecastManager().set_overforecasted()
        msg = "BFT dowload complete"
        logger.info(msg)
        messages.info(self.request, msg)
