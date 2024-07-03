import csv
import locale
import logging
import os
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime

import numpy as np
import pandas as pd
from django.contrib import messages
from django.db import IntegrityError

from bft.conf import QUARTERKEYS
from bft.models import (BftUser, CapitalInYear, CapitalNewYear, CapitalProject,
                        CapitalYearEnd, CostCenter, CostCenterAllocation,
                        CostCenterManager, Fund, FundCenter,
                        FundCenterAllocation, FundCenterManager, FundManager,
                        LineForecastManager, LineItem, LineItemImport, Source,
                        SourceManager)
from main.settings import BASE_DIR

logger = logging.getLogger("uploadcsv")


class UploadProcessor(ABC):
    class Meta:
        abstract = True

    def __init__(self, filepath, user: BftUser, request=None) -> None:
        self.filepath = filepath
        self.user = user
        self.header = None
        self.request = request

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
            logger.info(f"Validated FY match for allocation upload, {self.fy}, {self.quarter}")

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
            msg = f"Invalid quarter {self.quarter}, expected one of {QUARTERKEYS}."
            logger.error(msg)
            raise ValueError(msg)

        quarters = data.to_numpy()
        unique = (quarters[0] == quarters).all()
        if not unique:
            msg = f"Quarters not all matching. {self.user.username}, {self.fy}, {self.quarter}"
            logger.error(msg)
            raise ValueError(msg)
        elif int(quarters[0]) != int(self.quarter):
            msg = f"Error allocation upload. Quarter data does not match request ({quarters[0]} does not match {self.quarter})"
            logger.error(msg)
            raise ValueError(msg)
        else:
            logger.info(f"Validated Quarter match for allocation upload, {self.fy}, {self.quarter}")

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
        counter = 0
        for item in _dict:
            item["fund"] = FundManager().fund(item["fund"])
            item["fundcenter"] = FundCenterManager().fundcenter(item["fundcenter"])
            item["owner"] = self.user
            alloc = FundCenterAllocation(**item)
            try:
                alloc.save()
                counter += 1
                logger.info(f"Uploaded fund center allocation {alloc.fundcenter} - ${alloc.amount}.")
            except IntegrityError as err:
                msg = f"Saving fund center allocation {item} generates {err}"
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} fund center allocation(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


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
        counter = 0
        for item in _dict:
            item["fund"] = FundManager().fund(item["fund"])
            item["costcenter"] = CostCenterManager().cost_center(item["costcenter"])
            item["owner"] = self.user
            alloc = CostCenterAllocation(**item)
            try:
                alloc.save()
                counter += 1
                logger.info(f"Uploaded cost center allocation {alloc.costcenter} - ${alloc.amount}.")
            except IntegrityError as err:
                msg = f"Saving cost center allocation {item} generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} cost center allocation(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


class FundProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "fund,name,vote\n"

    def _find_duplicate_fund(self, funds: pd.DataFrame) -> pd.DataFrame:
        funds["fund"] = funds["fund"].str.lower()
        duplicates = funds[funds.duplicated(subset=["fund"], keep=False) == True]
        if duplicates.empty:
            return pd.DataFrame
        else:
            return duplicates

    def main(self, request=None):
        if not self.header_good():
            msg = f"Fund upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return

        df = self.dataframe()
        duplicates = self._find_duplicate_fund(df)
        if not duplicates.empty and request:
            messages.error(request, f"Duplicate funds have been detected: {duplicates.to_html()}")
            return

        _dict = self.as_dict(df)
        counter = 0
        for item in _dict:
            fund = Fund(**item)
            try:
                fund.save()
                counter += 1
                logger.info(f"Uploaded Fund {fund.fund}.")
            except IntegrityError as err:
                msg = f"Saving fund {item} generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} funds(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


class SourceProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "source\n"

    def _find_duplicate_source(self, sources: pd.DataFrame) -> pd.DataFrame:
        sources["source"] = sources["source"].str.lower()
        duplicates = sources[sources.duplicated(subset=["source"], keep=False) == True]
        if duplicates.empty:
            return pd.DataFrame
        else:
            return duplicates

    def main(self, request=None):
        if not self.header_good():
            msg = f"Source upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        duplicates = self._find_duplicate_source(df)
        if not duplicates.empty and request:
            messages.error(request, f"Duplicate sources have been detected: {duplicates.to_html()}")
            return

        _dict = self.as_dict(df)
        counter = 0
        for item in _dict:
            source = Source(**item)
            try:
                source.save()
                counter += 1
                logger.info(f"Uploaded Source {source.source}.")
            except IntegrityError as err:
                msg = f"Saving source {item} generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} sources(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


class FundCenterProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "fundcenter_parent,fundcenter,shortname\n"

    def _find_duplicate_fundcenters(self, fundcenters: pd.DataFrame) -> pd.DataFrame:
        fundcenters["fundcenter"] = fundcenters["fundcenter"].str.lower()
        duplicates = fundcenters[fundcenters.duplicated(subset=["fundcenter"], keep=False) == True]
        if duplicates.empty:
            return pd.DataFrame
        else:
            return duplicates

    def main(self, request=None):
        if not self.header_good():
            msg = f"Fund Centers upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return
        df = self.dataframe()
        duplicates = self._find_duplicate_fundcenters(df)
        if not duplicates.empty and request:
            messages.error(request, f"Duplicate fund centers have been detected: {duplicates.to_html()}")
            return

        _dict = self.as_dict(df)
        counter = 0
        for item in _dict:
            if item["fundcenter_parent"] == "":
                item["fundcenter_parent"] = None
            else:
                item["fundcenter_parent"] = FundCenterManager().fundcenter(item["fundcenter_parent"])
            item_obj = FundCenter(**item)
            try:
                item_obj.save()
                counter += 1
                logger.info(f"Uploaded fund center {item_obj.fundcenter}.")
            except IntegrityError as err:
                msg = f"Saving fund center {item}  generates {err}."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} fund center(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


class CapitalProjectProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "project_no,shortname,fundcenter,note\n"

    def _find_duplicate_project_no(self, projects: pd.DataFrame) -> pd.DataFrame:
        projects["project_no"] = projects["project_no"].str.lower()
        duplicates = projects[projects.duplicated(subset=["project_no"], keep=False) == True]
        if duplicates.empty:
            return pd.DataFrame
        else:
            return duplicates

    def _assign_fundcenter(self, projects: dict, request=None) -> dict | None:
        for item in projects:  # assign parent, fund and source to everyone before saving
            parent = FundCenterManager().fundcenter(item["fundcenter"])
            if not parent:
                msg = f"Capaital Project {item['project_no']} parent ({item['fundcenter']}) does not exist, no capital projects have been recorded."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
                return
            item["fundcenter"] = parent
        return projects

    def main(self, request=None):
        if not self.header_good():
            msg = f"Capaital project upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return

        df = self.dataframe()
        duplicates = self._find_duplicate_project_no(df)
        if not duplicates.empty and request:
            messages.error(request, f"Duplicate project numbers have been detected: {duplicates.to_html()}")
            return

        _dict = self.as_dict(df)
        if not self._assign_fundcenter(_dict, request):
            return

        counter = 0
        for item in _dict:
            item_obj = CapitalProject(**item)
            try:
                item_obj.save()
                counter += 1
                logger.info(f"Uploaded capital project {item_obj.project_no}.")
            except IntegrityError as err:
                msg = f"Saving capital project {item} generates {err}"
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} capital project(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


class CapitalProjectForecastProcessor(UploadProcessor):
    class Meta:
        abstract = True

    def __init__(self, filepath, user: BftUser, request=None) -> None:
        UploadProcessor.__init__(self, filepath, user, request)

    def _find_duplicates(self, df: pd.DataFrame, extra_subset: list = None) -> pd.DataFrame:
        subset = ["capital_project", "fund", "fy", "commit_item"]
        if extra_subset:
            subset.extend(extra_subset)
        duplicates = df[
            df.duplicated(
                keep=False,
                subset=subset,
            )
        ]
        if not duplicates.empty:
            msg = "Duplicate Fund-FY-Project have been detected in source data:"
            if self.request:
                messages.error(self.request, f"{msg} {duplicates.to_html()}")
            else:
                print(msg)
                print(duplicates)
        return duplicates

    def _assign_capital_project(self, capital_forecasts: dict, request=None) -> dict | None:
        for item in capital_forecasts:  # assign fund center to everyone before saving
            obj = CapitalProject.objects.get(project_no=item["capital_project"].upper())
            if not obj:
                msg = f"Project {item['capital_project']} does not exist, no capital forecasts have been recorded."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
                return
            item["capital_project"] = obj
        return capital_forecasts

    def _assign_fund(self, capital_forecasts: dict, request=None) -> dict | None:
        for item in capital_forecasts:  # assign fund to everyone before saving
            fund = FundManager().fund(item["fund"])
            if not fund:
                msg = f"Project {item['project_no']} fund ({item['fund']}) does not exist, no capital Forecasts have been recorded."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
                return
            item["fund"] = fund
        return capital_forecasts


# CapitalProjectNewYearProcessor, CapitalProjectInYearProcessor, CapitalProjectYearEndProcessor are very much alike
# Probably worth rework in one class at one point, but that works for now.
class CapitalProjectNewYearProcessor(CapitalProjectForecastProcessor):
    def __init__(self, filepath, user: BftUser, request=None) -> None:
        CapitalProjectForecastProcessor.__init__(self, filepath, user, request)
        self.header = "capital_project,fund,fy,commit_item,initial_allocation\n"

    def main(self):
        if not self.header_good():
            msg = "New year capital project forecast upload. Invalid columns header"
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
                return

        df = self.dataframe()
        duplicates = self._find_duplicates(df)
        if not duplicates.empty:
            return

        _dict = self.as_dict(df)
        if not self._assign_capital_project(_dict, self.request) or not self._assign_fund(
            _dict, self.request
        ):
            return

        counter = 0
        for item in _dict:
            obj = CapitalNewYear(**item)
            try:
                obj.save()
                counter += 1
                logger.info(f"Uploaded Capital Forecasting New Year {obj.fund}.")
            except IntegrityError as err:
                msg = f"Saving New Year Capital Forecasting {item} generates {err}."
                logger.warn(msg)
                if self.request:
                    messages.error(self.request, msg)
        if counter:
            msg = f"{counter} New Year Capital Forecasts(s) have been uploaded."
            if self.request:
                messages.info(self.request, msg)
            else:
                print(msg)


class CapitalProjectInYearProcessor(CapitalProjectForecastProcessor):
    def __init__(self, filepath, user: BftUser, request=None) -> None:
        CapitalProjectForecastProcessor.__init__(self, filepath, user, request)
        self.header = "capital_project,fund,fy,quarter,commit_item,allocation,le,mle,he,spent,co,pc,fr\n"

    def main(self):
        if not self.header_good():
            msg = "Capital project forecast upload. Invalid columns header"
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
                return

        df = self.dataframe()
        duplicates = self._find_duplicates(df, extra_subset=["quarter"])
        if not duplicates.empty:
            return

        _dict = self.as_dict(df)
        if not self._assign_capital_project(_dict, self.request) or not self._assign_fund(
            _dict, self.request
        ):
            return

        counter = 0
        for item in _dict:
            obj = CapitalInYear(**item)
            try:
                obj.save()
                counter += 1
                logger.info(f"Uploaded Capital Forecasting In Year {obj.fund}.")
            except IntegrityError as err:
                msg = f"Saving In Year Capital Forecasting {item} generates {err}."
                logger.warn(msg)
                if self.request:
                    messages.error(self.request, msg)
        if counter:
            msg = f"{counter} In Year Capital Forecasts(s) have been uploaded."
            if self.request:
                messages.info(self.request, msg)
            else:
                print(msg)


class CapitalProjectYearEndProcessor(CapitalProjectForecastProcessor):
    def __init__(self, filepath, user: BftUser, request=None) -> None:
        CapitalProjectForecastProcessor.__init__(self, filepath, user, request)
        self.header = "capital_project,fund,fy,commit_item,ye_spent\n"

    def main(self):
        if not self.header_good():
            msg = "Year end capital project forecast upload. Invalid columns header"
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
                return

        df = self.dataframe()
        duplicates = self._find_duplicates(df)
        if not duplicates.empty:
            return

        _dict = self.as_dict(df)
        if not self._assign_capital_project(_dict, self.request) or not self._assign_fund(
            _dict, self.request
        ):
            return

        counter = 0
        for item in _dict:
            obj = CapitalYearEnd(**item)
            try:
                obj.save()
                counter += 1
                logger.info(f"Uploaded Capital Forecasting Year End {obj.fund}.")
            except IntegrityError as err:
                msg = f"Saving Year End Capital Forecasting {item} generates {err}."
                logger.warn(msg)
                if self.request:
                    messages.error(self.request, msg)
        if counter:
            msg = f"{counter} {__class__.__name__} Year End Capital Forecasts(s) have been uploaded."
            if self.request:
                messages.info(self.request, msg)
            else:
                print(msg)


class CostCenterProcessor(UploadProcessor):
    def __init__(self, filepath, user: BftUser) -> None:
        UploadProcessor.__init__(self, filepath, user)
        self.header = "costcenter_parent,costcenter,shortname,isforecastable,isupdatable,source,fund\n"

    def _find_duplicate_costcenters(self, costcenters: pd.DataFrame) -> pd.DataFrame:
        costcenters["costcenter"] = costcenters["costcenter"].str.lower()
        duplicates = costcenters[costcenters.duplicated(subset=["costcenter"], keep=False) == True]
        if duplicates.empty:
            return pd.DataFrame
        else:
            return duplicates

    def _assign_fundcenter(self, costcenters: dict, request=None) -> dict | None:
        for item in costcenters:  # assign parent, fund and source to everyone before saving
            parent = FundCenterManager().fundcenter(item["costcenter_parent"])
            if not parent:
                msg = f"Cost center {item['costcenter']} parent ({item['costcenter_parent']}) does not exist, no cost centers have been recorded."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
                return
            item["costcenter_parent"] = parent
        return costcenters

    def _assign_fund(self, costcenters: dict, request=None) -> dict | None:
        for item in costcenters:  # assign parent, fund and source to everyone before saving
            fund = FundManager().fund(item["fund"])
            if not fund:
                msg = f"Cost center {item['costcenter']} fund ({item['fund']}) does not exist, no cost centers have been recorded."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
                return
            item["fund"] = fund
        return costcenters

    def _assign_source(self, costcenters: dict, request=None) -> dict | None:
        for item in costcenters:  # assign parent, fund and source to everyone before saving
            source = SourceManager().source(item["source"])
            if not source:
                msg = f"Cost center {item['costcenter']} source ({item['source']}) does not exist, no cost centers have been recorded."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
                return
            item["source"] = source
        return costcenters

    def main(self, request=None):
        if not self.header_good():
            msg = f"Cost Centers upload by {self.user.username}, Invalid columns header"
            logger.error(msg)
            if request:
                messages.error(request, msg)
                return

        df = self.dataframe()
        duplicates = self._find_duplicate_costcenters(df)
        if not duplicates.empty and request:
            messages.error(request, f"Duplicate cost centers have been detected: {duplicates.to_html()}")
            return

        _dict = self.as_dict(df)
        if not self._assign_fundcenter(_dict, request):
            return
        if not self._assign_fund(_dict, request):
            return
        if not self._assign_source(_dict, request):
            return

        counter = 0
        for item in _dict:
            item_obj = CostCenter(**item)
            try:
                item_obj.save()
                counter += 1
                logger.info(f"Uploaded cost center {item_obj.costcenter}.")
            except IntegrityError as err:
                msg = f"Saving cost center {item} generates {err}"
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
        if counter:
            msg = f"{counter} cost center(s) have been uploaded."
            if request:
                messages.info(request, msg)
            else:
                print(msg)


class LineItemProcessor(UploadProcessor):
    """
    LineItemProcessor class process the DND Cost Center encumbrance report.  It
    creates a csv file and populate the table using LineItemImport class.

    Raises:
        ValueError: If no encumbrance file name is provided.
        FileNotFoundError: If the encumbrance file is not found
    """

    #: Number of columns expected in the DND Cost Center Encumbrance Report
    COLUMNS = 22  # Includes empty columns at beginning and end of row
    #: Location where the csv version of the DND Cost Center Encumbrance Report is saved.
    CSVFILE = os.path.join(BASE_DIR, "drmis_data/encumbrance.csv")
    #: Location where DRMIS reports are saved.
    DRMIS_DIR = os.path.join(BASE_DIR, "drmis_data")
    #: Columnc names and order as found in the DND Cost Center Encumbrance report and used to create the CSV file.
    CSVFIELDS = "|docno|lineno|acctassno|spent|balance|workingplan|fundcenter|fund|costcenter|internalorder|doctype|enctype|linetext|predecessordocno|predecessorlineno|reference|gl|duedate|vendor|createdby|"

    def __init__(self, filepath=None, request=None):
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        if filepath is None:
            raise ValueError("No file name provided")
        print("FILEPATH: ", filepath)
        # filepath = os.path.join(self.DRMIS_DIR, filepath)
        print("DRMIS DIR: ", self.DRMIS_DIR)
        print("FILEPATH: ", filepath)
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
            "fy": "Base Fiscal Year :",
            "fund_center": "Funds Center :",
            "header": "|Document N|Line Numbe|",
            "report": "DND Cost Center Encumbrance Report",
        }
        self.data = {
            "fy": None,  # FY read on report header
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
            parts = line.split(":")
            if len(parts) == 2:
                self.data["fc"] = parts[1].strip().split(" ")[0].upper()
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
            parts = line.split(":")
            if len(parts) == 2:
                self.data["fy"] = parts[1].strip()
        # print(f"Foud FY {self.data['fy']}")
        return self.data["fy"]

    def clean_header(self, header: list) -> None:
        """Strips empty first and last column and strips all blanks in column elements

        Args:
            header (list): The column header list to clean
        """
        if header[-1] == "" or header[-1] == "\n":
            header.pop()
        if header[0] == "" or header[-1] == "\n":
            header.pop(0)
        for _, e in enumerate(header):
            e = e.strip()
            self.data["header"] += [e]

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
        line_len = len(csv)
        if line_len == 20:
            return csv
        else:
            raise AttributeError(
                f"Invalid line encountered in Encumbrance Report. Expected 20 elements, got {line_len}: {'|'.join(csv[:4])}"
            )

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
        if len(line) > 0 and re.search(r"^\|[A-Z0-9 ]{10}\|[\s\d]{10}\|", line):
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
        """Import CSV Encumbrance file in the LineItemImport Table"""

        def str2float(n):
            try:
                return locale.atof(n)
            except ValueError:
                logger.fatal(f"Failed to convert '{n}' to float")
                sys.exit()

        def str2date(s):
            if s == "":
                return None
            try:
                d = datetime.strptime(s, "%Y.%m.%d")
                return d
            except ValueError:
                logger.fatal(f"Failed to convert {s} as date")
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

    def spent_in_fr_pc(self) -> bool:
        # Must return false for clean result
        df = pd.read_csv(self.CSVFILE, usecols=["spent", "doctype", "enctype"])
        fr_has_spent = not df.query("doctype == 'FR' & spent > 0 ").empty
        pc_has_spent = not df.query("doctype == 'PC' & spent > 0 ").empty
        return all([fr_has_spent, pc_has_spent])

    def _set_data(self) -> bool:
        if not self.filepath:
            raise ValueError("Encumbrance report not defined.")

        with open(self.filepath, encoding="windows-1252") as lines:
            is_set = [False, False]
            for line in lines:
                if self.data["fy"] is None:
                    is_set[0] = self.find_base_fy(line)
                if self.data["fc"] is None:
                    is_set[1] = self.find_fund_center(line)
                if all(is_set):
                    break

            logger.info(f"Fiscal Year : {self.data['fy']}")
            logger.info(f"Fund Center : {self.data['fc']}")
            if not all(is_set):
                msg = f"Line Items upload by {self.user}.  Could not find FY, FC or report in report header."
                logger.error(msg)
                if self.request:
                    messages.error(self.request, msg)
        return all(is_set)

    def _fundcenter_matches_report(self):
        if not self.request:
            return True  # This means that we are uploading through the command line.
        if self.fundcenter != self.data["fc"]:
            msg = f"{self.fundcenter} does not match report found in dataset: {self.data['fc']}"
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
            return False
        return True

    def _do_preliminary_checks(self) -> bool:
        logger.info(f"Begin Upload processing by {self.user}")
        if not self._set_data():
            logger.warn("Failed to set data.  Something is wrong with the encubrance report.")
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

        return True

    def main(self) -> bool:
        if not self._do_preliminary_checks():
            return False
        if self.spent_in_fr_pc():
            raise ValueError("Encumbrance Report contains spent amount in either FR or PC elements")
        self.csv2table()
        linecount = LineItemImport.objects.count()
        logger.info(f"{linecount} lines have been written to Encumbrance import table")

        li = LineItem()

        orphan = li.get_orphan_lines()
        li.mark_orphan_lines(orphan)

        li.import_lines()
        li.set_fund_center_integrity()
        li.set_doctype()
        LineForecastManager().set_encumbrance_history_record()
        # LineForecastManager().set_unforecasted_to_spent()
        LineForecastManager().set_underforecasted()
        LineForecastManager().set_overforecasted()
        msg = "BFT dowload complete"
        logger.info(msg)
        if self.request:
            messages.info(self.request, msg)


class CostCenterLineItemProcessor(LineItemProcessor):
    def __init__(self, filepath, costcenter: str, fundcenter: str, request=None):
        super().__init__(filepath, request)
        self.costcenter = costcenter.upper()
        self.fundcenter = fundcenter.upper()
        self.costcenter_obj = CostCenter.objects.get(costcenter=self.costcenter)

    def all_costcenter_are_equals(self) -> bool:
        """Ensures the the encumbrance report lines are related to one single cost center.  Verification is done from the csv file."""
        df = pd.read_csv(BASE_DIR / "drmis_data/encumbrance.csv")
        cc = df["costcenter"]
        cc_set = set(cc.to_list())
        set_size = len(cc_set)
        msg = None
        if set_size > 10:
            msg = "There are more that 10 different cost centers in the report."
        elif set_size > 1:
            msg = f"There are more that one cost center in the report. Found {', '.join(cc_set)}"
        if msg:
            logger.error(msg)
            if self.request:
                messages.error(self.request, msg)
        return set_size == 1

    def main(self) -> bool:
        logger.info(f"Begin Cost Center Upload processing by {self.user}")
        if not self.costcenter_obj.isupdatable:
            messages.warning(
                self.request,
                f"{self.costcenter} is not updatable.  You must change the Updatable status first to proceed.",
            )
            return False
        if not self._set_data():
            logger.warning("Failed to set data")
            return False

        if not self._fundcenter_matches_report():
            logger.error("Fund center report does not match")
            return False

        if not self.is_dnd_cost_center_report():
            logger.error("We do not have a DND Cost center encumbrance report")
            return False

        logger.info("We have a DND Cost center encumbrance report.")

        if self.find_header_line() == 0:
            return False

        if self.write_encumbrance_file_as_csv() == 0:
            return False
        if not self.all_costcenter_are_equals():
            return False

        if self.missing_fund():
            return False

        if not self.all_costcenter_are_equals():
            return False

        if self.missing_costcenters():
            return False

        self.csv2table()
        linecount = LineItemImport.objects.count()
        logger.info(f"{linecount} lines have been written to Encumbrance import table")

        li = LineItem()

        orphan = li.get_orphan_lines(costcenter=self.costcenter_obj)
        li.mark_orphan_lines(orphan)

        li.import_lines()
        li.set_fund_center_integrity()
        li.set_doctype()
        LineForecastManager().set_encumbrance_history_record(self.costcenter_obj)
        # LineForecastManager().set_unforecasted_to_spent()
        LineForecastManager().set_underforecasted(self.costcenter_obj)
        LineForecastManager().set_overforecasted(self.costcenter_obj)
        msg = "BFT dowload complete"
        logger.info(msg)
        if self.request:
            messages.info(self.request, msg)
