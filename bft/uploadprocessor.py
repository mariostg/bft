from abc import abstractmethod
from django.contrib import messages
from users.models import BftUser
from django.db import models, IntegrityError
import logging
import pandas as pd
import numpy as np
from bft.conf import QUARTERKEYS
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

logger = logging.getLogger("uploadcsv")


class UploadProcessor:
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
            except IntegrityError:
                msg = f"Saving fund center {item} would create duplicate entry."
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
            except IntegrityError:
                msg = f"Saving cost center {item} would create duplicate entry."
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
            except IntegrityError:
                msg = f"Saving fund {item} would create duplicate entry."
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
            except IntegrityError:
                msg = f"Saving source {item} would create duplicate entry."
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
            except IntegrityError:
                msg = f"Saving fund center {item} would create duplicate entry."
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
            except IntegrityError:
                msg = f"Saving cost center {item} would create duplicate entry."
                logger.warn(msg)
                if request:
                    messages.error(request, msg)
