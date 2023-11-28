from datetime import datetime
from abc import abstractmethod
import numpy as np

np.set_printoptions(suppress=True)
from django.contrib import messages
from django.db import models, IntegrityError
from django.db.models import QuerySet
from django.conf import settings
from django.forms.models import model_to_dict
import pandas as pd
from pandas.io.formats.style import Styler
from bft.conf import YEAR_CHOICES, QUARTERS, QUARTERKEYS, YEAR_VALUES
from bft import exceptions
from utils.dataframe import BFTDataFrame
from users.models import BftUser
import logging

logger = logging.getLogger("uploadcsv")


class FundManager(models.Manager):
    def fund(self, fund: str):
        try:
            obj = Fund.objects.get(fund__iexact=fund)
        except Fund.DoesNotExist:
            return None
        return obj

    def pk(self, pk: int):
        try:
            obj = Fund.objects.get(pk=pk)
        except Fund.DoesNotExist:
            return None
        return obj

    def exists(self, fund: str) -> bool:
        return Fund.objects.filter(fund=fund).exists()

    def get_request(self, request) -> str | None:
        print(request)
        fund = request.GET.get("fund")
        if fund:
            fund = fund.upper()
            if not FundManager().exists(fund):
                messages.info(request, "Fund specified does not exist.")
            return fund
        else:
            return None


class Fund(models.Model):
    fund = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=30)
    vote = models.CharField(max_length=1)
    download = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fund} - {self.name}"

    class Meta:
        ordering = ["-download", "fund"]
        verbose_name_plural = "Funds"

    def save(self, *args, **kwargs):
        self.fund = self.fund.upper()
        super(Fund, self).save(*args, **kwargs)

    objects = FundManager()


class SourceManager(models.Manager):
    def source(self, source: str):
        try:
            obj = Source.objects.get(source__iexact=source)
        except Source.DoesNotExist:
            return None
        return obj

    def pk(self, pk: int):
        try:
            obj = Source.objects.get(pk=pk)
        except Source.DoesNotExist:
            return None
        return obj


class Source(models.Model):
    source = models.CharField(max_length=24, unique=True)

    def __str__(self):
        return f"{self.source}"

    class Meta:
        verbose_name_plural = "Sources"

    def save(self, *args, **kwargs):
        self.source = self.source.capitalize()
        super(Source, self).save(*args, **kwargs)

    objects = SourceManager()


class FundCenterManager(models.Manager):
    def fundcenter(self, fundcenter: str) -> "FundCenter | None":
        fundcenter = fundcenter.upper()
        try:
            obj = FundCenter.objects.get(fundcenter__iexact=fundcenter)
        except FundCenter.DoesNotExist:
            return None
        return obj

    def pk(self, pk: int):
        try:
            obj = FundCenter.objects.get(pk=pk)
        except FundCenter.DoesNotExist:
            return None
        return obj

    def get_sub_alloc(self, parent_alloc: "FundCenterAllocation") -> "FundCenterAllocation":
        seq = [s["sequence"] for s in self.get_direct_descendants(parent_alloc.fundcenter)]
        dd = FundCenter.objects.filter(sequence__in=seq)
        return FundCenterAllocation.objects.filter(
            fundcenter__in=dd,
            fy=parent_alloc.fy,
            fund=parent_alloc.fund,
            quarter=parent_alloc.quarter,
        )

    def sequence_exist(self, sequence):
        return FundCenter.objects.filter(sequence=sequence).exists()

    def fund_center_exist(self, fc):
        return FundCenter.objects.filter(fundcenter=fc).exists()

    def fund_center_dataframe(self, data: QuerySet) -> pd.DataFrame:
        """Prepare a pandas dataframe of the fund centers as per financial structure.
        Columns are renamed with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of fund centers.
        """
        if not data.count():
            return pd.DataFrame()
        df = BFTDataFrame(FundCenter).build(data)

        df["Fundcenter_parent_ID"] = df["Fundcenter_parent_ID"].fillna(0).astype("int")
        return df

    def allocation_dataframe(
        self,
        fundcenter: "FundCenter|str" = None,
        fund: "Fund|str" = None,
        fy: int = None,
        quarter: str = None,
    ) -> pd.DataFrame:
        data = FundCenterAllocation.objects.fundcenter(fundcenter).fund(fund).fy(fy).quarter(quarter)
        rename_columns = {
            "amount": "Allocation",
            "fy": "FY",
            "quarter": "Quarter",
            "fundcenter__fundcenter": "Fund Center",
            "fund__fund": "Fund",
        }
        try:
            df = pd.DataFrame(data).rename(columns=rename_columns)
        except ValueError:
            if not isinstance(data, dict):
                data = model_to_dict(data)
            df = pd.DataFrame([data]).rename(columns=rename_columns)

        return df

    def get_direct_descendants(self, fundcenter: "FundCenter|str") -> list | None:
        if not fundcenter:
            return []
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        return self.get_fund_centers(fundcenter) + self.get_cost_centers(fundcenter)

    def get_direct_descendants_dataframe(self, fundcenter: "FundCenter|str") -> list | None:
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        fc = pd.DataFrame(self.get_fund_centers(fundcenter))
        cc = pd.DataFrame(self.get_cost_centers(fundcenter))
        return pd.concat([fc, cc])

    def get_fund_centers(self, parent: "FundCenter|str") -> list:
        if isinstance(parent, str):
            parent = self.fundcenter(parent)
        return list(FundCenter.objects.filter(fundcenter_parent=parent).values())

    def get_cost_centers(self, parent: "FundCenter|str") -> list:
        if isinstance(parent, str):
            parent = self.fundcenter(parent)
        return list(CostCenter.objects.filter(costcenter_parent=parent).values())

    def exists(self, fundcenter: str) -> bool:
        return FundCenter.objects.filter(fundcenter=fundcenter).exists()

    def get_request(self, request) -> str | None:
        fundcenter = request.GET.get("fundcenter")
        if fundcenter:
            fundcenter = fundcenter.upper()
            if not FundCenterManager().exists(fundcenter):
                messages.info(request, f"Fund Center {fundcenter} does not exist.")
            return fundcenter
        else:
            return None


class FinancialStructureManager(models.Manager):
    def FundCenters(self, fundcenter: str = None, seqno: str = None, fcid: int = None):
        try:
            if fundcenter:
                obj = FundCenter.objects.filter(fundcenter=fundcenter.upper())
            elif seqno:
                obj = FundCenter.objects.filter(sequence__startswith=seqno)
            elif fcid:
                obj = FundCenter.objects.filter(id=fcid)
            else:
                obj = FundCenter.objects.all()
        except exceptions.FundCenterExceptionError(fundcenter=fundcenter, seqno=seqno):
            return None
        return obj

    def has_children(self, fundcenter: "FundCenter|str") -> int:
        if type(fundcenter) == str:
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return self.has_cost_centers(fundcenter) + self.has_fund_centers(fundcenter)

    def has_fund_centers(self, fundcenter: "FundCenter|str") -> int:
        if type(fundcenter) == str:
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return FundCenter.objects.filter(fundcenter_parent=fundcenter).count()

    def has_cost_centers(self, fundcenter: "FundCenter|str") -> int:
        if type(fundcenter) == str:
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return CostCenter.objects.filter(costcenter_parent=fundcenter).count()

    def is_child_of(self, parent: "FundCenter", child: "FundCenter | CostCenter") -> bool:
        """Check if child object is a direct descendant of parent

        Args:
            parent (FundCenter): A fund center object.
            child (FundCenter | CostCenter): A fund center or cost center object

        Returns:
            bool: True is child is direct descendant of parent.
        """
        if isinstance(child, FundCenter):
            try:
                _parent = FundCenter.objects.get(fundcenter=parent.fundcenter)
            except FundCenter.DoesNotExist:
                return False
            try:
                _child = FundCenter.objects.get(fundcenter=child.fundcenter)
            except FundCenter.DoesNotExist:
                return False
            return self.is_sequence_child_of(_parent.sequence, _child.sequence)
            # return _parent.fundcenter == _child.fundcenter_parent.fundcenter
        elif isinstance(child, CostCenter):
            try:
                _parent = FundCenter.objects.get(fundcenter=parent.fundcenter)
            except FundCenter.DoesNotExist:
                return False
            try:
                _child = CostCenter.objects.get(costcenter=child.costcenter)
            except CostCenter.DoesNotExist:
                return False
            return _parent.fundcenter == _child.costcenter_parent.fundcenter
        else:
            return False

    def is_descendant_of(self, parent: "FundCenter", child: "FundCenter | CostCenter") -> bool:
        """Check if child is a direct descendant of parent.

        Args:
            parent (FundCenter): A Fund Center object which is potential parent.
            child (FundCenter | CostCenter): A Fund Center or Cost Center object that could be a descendant.

        Returns:
            bool: Returns True if the child argument is a descendant of parent argument.
        """
        return self.is_sequence_descendant_of(parent.sequence, child.sequence)

    def sequence_exists(self, seqno: str = None) -> bool:
        """Detrmine if the given sequence number exists in the system.

        Args:
            seqno (str, optional): A string representing a valid sequence number. Defaults to None.

        Returns:
            bool: Returns True if the sequence number exists in the system.
        """
        if seqno:
            return seqno in [x.sequence for x in self.FundCenters(seqno=seqno)]

    def set_parent(self, fundcenter_parent: "FundCenter" = None, costcenter_child: bool = False) -> str:
        """
        Create a sequence number by refering to the sequence numbers of the family of fundcenter_parent.
        The sequence number created contains the parent sequence plus the portion of the child.

        Args:
            fundcenter_parent (FundCenter, optional): The fund center that is the parent of the sub center that need a sequence number. Defaults to None.
            costcenter_child (bool, optional): If parent is for cost center, costcenter_child must be True. This will affect the way the sequence number is created. Defaults to False.

        Returns:
            str: A string the represents the child sequence number.
        """
        if fundcenter_parent == None:
            last_root = FinancialStructureManager().last_root()
            if not last_root:
                parent = "1"
            else:
                parent = str(int(last_root) + 1)
            return parent
        new_seq = self.create_child(fundcenter_parent.fundcenter, costcenter_child)
        return new_seq

    def is_sequence_descendant_of(self, seq_parent: str, seq_child: str) -> bool:
        """Compare two sequence numbers to determine if one is a descendant of the other.

        Args:
            seq_parent (str): The sequence number of the parent.
            seq_child (str): The sequence number of the descendant.

        Returns:
            bool: Returns True if the child sequence number is contained in the parent sequence number.
        """
        if ".0." in seq_parent or seq_parent.endswith(".0"):
            raise AttributeError("Parent connot contains .0. in sequence number")
        if len(seq_child) == len(seq_parent):
            return False
        if seq_child.startswith(seq_parent):
            return True
        return False

    def is_sequence_child_of(self, seq_parent: str, seq_child: str) -> bool:
        """Compare two sequence numbers to determine if one is a direct descendant of the other.

        Args:
            seq_parent (str): The sequence number of the parent.
            seq_child (str): Teh sequence number of the child.

        Returns:
            bool: Returns True if the child sequence number is contained in the parent sequence number.
        """

        if not self.is_sequence_descendant_of(seq_parent, seq_child):
            return False
        if ".0." not in seq_child and len(seq_child) - 2 == len(seq_parent):
            return True
        if ".0." in seq_child:
            seq_child = seq_child.replace(".0.", ".")
            return self.is_sequence_child_of(seq_parent, seq_child)
        return False

    def get_fundcenter_descendants(self, fundcenter: "FundCenter") -> QuerySet | None:
        """Create a QuerySet of fundcenters that are descendants of the fund center passed as argument.

        Args:
            fundcenter (FundCenter): A fund center object which the descendants are desired.

        Returns:
            QuerySet: Returns a QuerySet of FundCenter objects that are descendants.  Returns None if no descendants exists.
        """
        try:
            return FundCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        except AttributeError:
            return None

    def get_fund_center_cost_centers(self, fundcenter: "FundCenter") -> QuerySet | None:
        """Create a QuerySet of Cost Centers that are direct children of the given Fund Center.

        Args:
            fundcenter (FundCenter): A Fund Center object

        Returns:
            QuerySet | None: Returns a QuerySet of Cost Centers that are children.  Return None if there are no children.
        """
        cc = CostCenter.objects.filter(costcenter_parent=fundcenter)
        return cc

    def get_sequence_direct_descendants(self, seq_parent: str) -> list:
        """Provide a list of sequence numbers representing the direct descendants of
        the given parent sequence number.

        Args:
            seq_parent (str): the sequence number of the parent.

        Raises:
            exceptions.ParentDoesNotExistError: Will be raised if the parent is not found in the list.

        Returns:
            list: A list of sequence numbers that are direct descendants of the parent.  The parent is not included in the returned list.
        """
        family = list(self.FundCenters().values_list("sequence", flat=True))
        if CostCenter.objects.all().count():
            cc_seq = list(CostCenter.objects.values_list("sequence", flat=True))
            family = family + cc_seq
        if seq_parent not in family:
            raise exceptions.ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_sequence_child_of(seq_parent, d):
                descendants.append(d)
        return descendants

    def create_child(self, parent: str = None, costcenter_child: bool = False) -> str:
        from costcenter.models import FundCenterManager

        """Create a new sequence number to be attributed to a cost center or a fund center.

        Args:
            parent (str, optional): A string representing the parent Fund Center.
            Defaults to None.
            costcenter_child (bool, optional): If parent is for cost center, costcenter_child must be True. This will affect the way the sequence number is created. Defaults to False.

        Returns:
            str: The sequence number of the child.
        """
        FCM = FundCenterManager()
        parent = FCM.fundcenter(parent)
        if costcenter_child:
            children = FCM.get_cost_centers(parent)
        else:
            children = FCM.get_fund_centers(parent)
        if children == []:
            suffix = ".0.1" if costcenter_child else ".1"
            new_born = parent.sequence + suffix
            return new_born
        else:
            pass
        splitted = [i["sequence"].split(".") for i in children]
        splitted = np.array(splitted).astype(int)
        oldest = list(splitted.max(axis=0))
        new_born = oldest
        new_born[-1] = int(new_born[-1]) + 1
        new_born = [str(i) for i in new_born]
        new_born = ".".join(new_born)
        return new_born

    def last_root(self) -> str | None:
        """A root element is one where the sequence number does not contain a dot ('.').
        last_root function finds the highest sequence number amongst the root elements.

        Returns:
            str | None: The last sequence number assigned as a root element or None if there is no root element.
        """
        seq = list(FundCenter.objects.all().values_list("sequence", flat=True))
        if not seq:
            return None

        return str(max([int(s) for s in seq if "." not in s]))

    def new_root(self) -> str:
        lr = self.last_root()
        if not lr:
            return "1"
        return str(int(lr) + 1)

    def financial_structure_dataframe(self) -> pd.DataFrame:
        fc = FundCenterManager().fund_center_dataframe(FundCenter.objects.all())
        cc = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())
        if fc.empty or cc.empty:
            return pd.DataFrame()
        merged = pd.merge(
            fc,
            cc,
            how="left",
            left_on=["Fundcenter_ID", "FC Path", "Fund Center", "Fund Center Name"],
            right_on=["Costcenter_parent_ID", "FC Path", "Fund Center", "Fund Center Name"],
        )
        print(merged)
        merged = merged.fillna("")
        merged.set_index(
            ["FC Path", "Fund Center", "Fund Center Name", "Cost Center", "Cost Center Name"], inplace=True
        )
        merged.drop(
            [
                "Fundcenter_ID_x",
                "Fundcenter_ID_y",
                "Fundcenter_parent_ID_x",
                "Fundcenter_parent_ID_y",
                "Costcenter_ID",
                "Fund_ID",
                "Source_ID",
                "Costcenter_parent_ID",
            ],
            axis=1,
            inplace=True,
        )
        merged.sort_values(by=["FC Path"], inplace=True)

        return merged

    def financial_structure_styler(self, data: pd.DataFrame):
        def indent(s):
            return f"text-align:left;padding-left:{len(str(s))*4}px"

        html = Styler(data, uuid_len=0, cell_ids=False)
        table_style = [
            {"selector": "tbody:nth-child(odd)", "props": "background-color:red"},
        ]
        data = (
            html.applymap_index(indent, level=0)
            .set_table_attributes("class=fin-structure")
            .set_table_styles(table_style)
        )
        return data

    def CostCenters(self):
        pass

    def all(self):
        pass


class FundCenter(models.Model):
    fundcenter = models.CharField("Fund Center", max_length=6, unique=True)
    shortname = models.CharField("Fund Center Name", max_length=25, null=True, blank=True)
    sequence = models.CharField("FC Path", max_length=25, unique=True)
    level = models.SmallIntegerField("Level", default=0)
    fundcenter_parent = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="parent_fc",
        verbose_name="Fund Center Parent",
    )

    objects = FundCenterManager()

    def __str__(self):
        if self.fundcenter:
            return f"{self.fundcenter.upper()} - {self.shortname.upper()}"
        return ""

    class Meta:
        ordering = ["fundcenter"]
        verbose_name_plural = "Fund Centers"

    def save(self, *args, **kwargs):
        if self.fundcenter_parent == None:
            self.sequence = FinancialStructureManager().new_root()
        elif self.fundcenter_parent and self.fundcenter == self.fundcenter_parent.fundcenter:
            raise IntegrityError("Children Fund center cannot assign itself as parent")
        elif not FinancialStructureManager().is_child_of(self.fundcenter_parent, self):
            self.sequence = FinancialStructureManager().set_parent(self.fundcenter_parent)

        self.fundcenter = self.fundcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        self.level = len(self.sequence.split("."))
        super(FundCenter, self).save(*args, **kwargs)


class CostCenterManager(models.Manager):
    def cost_center(self, costcenter: str) -> "CostCenter|None":
        costcenter = costcenter.upper()
        try:
            cc = CostCenter.objects.get(costcenter=costcenter)
        except CostCenter.DoesNotExist:
            return None
        return cc

    def pk(self, pk: int):
        try:
            cc = CostCenter.objects.get(pk=pk)
        except CostCenter.DoesNotExist:
            return None
        return cc

    def get_sub_alloc(
        self, fc: FundCenter | str, fund: Fund | str, fy: int, quarter: int
    ) -> "CostCenterAllocation":
        if isinstance(fc, str):
            fc = FundCenterManager().fundcenter(fc)
        if isinstance(fund, str):
            fund = FundManager().fund(fund)
        cc = FinancialStructureManager().get_fund_center_cost_centers(fc)
        return CostCenterAllocation.objects.filter(
            costcenter__in=cc,
            fy=fy,
            fund=fund,
            quarter=quarter,
        )

    def cost_center_dataframe(self, data: QuerySet) -> pd.DataFrame:
        """Prepare a pandas dataframe of the cost centers as per financial structure.
        Columns are renamed with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of cost centers.
        """
        if not CostCenter.objects.exists():
            return pd.DataFrame()
        df = BFTDataFrame(CostCenter).build(data)
        fc_df = BFTDataFrame(FundCenter).build(FundCenter.objects.all())
        df = pd.merge(df, fc_df, how="left", left_on="Costcenter_parent_ID", right_on="Fundcenter_ID")
        return df

    def allocation_dataframe(
        self,
        costcenter: "CostCenter|str" = None,
        fund: "Fund|str" = None,
        fy: int = None,
        quarter: str = None,
    ) -> pd.DataFrame:
        """Prepare a pandas dataframe of the cost center allocations for the given FY and Quarter.
        Columns are renamed with a more friendly name. Column names are : Fund Center, Cost Center, Fund, Allocation, FY, and Quarter.

        Returns:
            pd.DataFrame: A dataframe of cost center allocations.
        """
        data = CostCenterAllocation.objects.costcenter(costcenter).fund(fund).fy(fy).quarter(quarter)
        if not data:
            return pd.DataFrame({})
        data = list(
            data.values(
                "costcenter__costcenter_parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
                "fy",
                "quarter",
            )
        )
        columns = {
            "amount": "Allocation",
            "fy": "FY",
            "quarter": "Quarter",
            "costcenter__costcenter": "Cost Center",
            "costcenter__costcenter_parent__fundcenter": "Fund Center",
            "fund__fund": "Fund",
        }
        df = pd.DataFrame(data).rename(columns=columns)
        return df

    def forecast_adjustment_dataframe(self) -> pd.DataFrame:
        if not ForecastAdjustment.objects.exists():
            return pd.DataFrame()
        data = list(
            ForecastAdjustment.objects.all().values(
                "costcenter__costcenter_parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
            )
        )
        columns = {
            "amount": "Forecast Adjustment",
            "costcenter__costcenter_parent__fundcenter": "Fund Center",
            "costcenter__costcenter": "Cost Center",
            "fund__fund": "Fund",
        }
        return pd.DataFrame(data).rename(columns=columns)

    def get_sibblings(self, parent: FundCenter | str):
        if type(parent) == str:
            parent = FundCenterManager().fundcenter(fundcenter=parent)
        return CostCenter.objects.filter(costcenter_parent=parent)


class CostCenter(models.Model):
    costcenter = models.CharField("Cost Center", max_length=6, unique=True)
    shortname = models.CharField("Cost Center Name", max_length=35, blank=True, null=True)
    fund = models.ForeignKey(Fund, on_delete=models.RESTRICT, default="", verbose_name="Fund")
    source = models.ForeignKey(Source, on_delete=models.RESTRICT, default="", verbose_name="Source")
    isforecastable = models.BooleanField("Is Forecastable", default=False)
    isupdatable = models.BooleanField("Is Updatable", default=False)
    note = models.TextField(null=True, blank=True)
    sequence = models.CharField("CC Path", max_length=25, unique=True, default="")
    costcenter_parent = models.ForeignKey(
        FundCenter,
        on_delete=models.RESTRICT,
        default="0",
        related_name="children",
        verbose_name="Cost Center Parent",
    )
    procurement_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        limit_choices_to={"procurement_officer": True},
    )
    objects = CostCenterManager()

    def __str__(self):
        return f"{self.costcenter.upper()} - {self.shortname}"

    class Meta:
        ordering = ["costcenter"]
        verbose_name_plural = "Cost Centers"

    def save(self, *args, **kwargs):
        if not FinancialStructureManager().is_child_of(self.costcenter_parent, self):
            self.sequence = FinancialStructureManager().set_parent(
                self.costcenter_parent, costcenter_child=True
            )
        # if self.costcenter_parent and self.costcenter == self.costcenter_parent.fundcenter:
        #     raise IntegrityError(
        #         f"Children Fund center cannot assign itself as parent {self.costcenter_parent.fundcenter}"
        #     )

        self.costcenter = self.costcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        super(CostCenter, self).save(*args, **kwargs)


class ForecastAdjustmentManager(models.Manager):
    def fundcenter_descendants(self, fundcenter: str, fund: str = None) -> dict:
        """Produce a dictionay of Forecast Adjustments including all descendants of the specified fund center.  The key element of each entry is the id of the cost center.

        Args:
            fundcenter (str): Fund Center
            fund (str): Fund.

        Returns:
            dict: A dictionary of forecast adjustments for all descendants of the specified fund center.
        """
        root = FundCenterManager().fundcenter(fundcenter)

        cc = CostCenter.objects.filter(sequence__startswith=root.sequence)
        fund = FundManager().fund(fund)
        if cc:
            fcst_adj = ForecastAdjustment.objects.filter(costcenter__in=cc, fund=fund)

            lst = {}
            d = {}
            for item in fcst_adj:
                _id = item.costcenter.id
                cc = item.costcenter
                pid = cc.costcenter_parent.id
                d = {
                    "Cost Element": cc.costcenter,
                    "Cost Element Name": cc.shortname,
                    "Fund Center ID": cc.id,
                    "Fund": cc.fund.fund,
                    "Parent ID": pid,
                    "Path": cc.sequence,
                    "Parent Path": cc.costcenter_parent.sequence,
                    "Parent Fund Center": cc.costcenter_parent.fundcenter,
                    "Forecast Adjustment": float(item.amount),
                    "Type": "CC",
                }
                lst[_id] = d

        return lst


class ForecastAdjustment(models.Model):
    costcenter = models.ForeignKey(
        CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center"
    )
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.costcenter} - {self.fund} - {self.amount}"

    class Meta:
        ordering = ["costcenter", "fund"]
        verbose_name_plural = "Forecast Adjustments"


class AllocationQuerySet(models.QuerySet):
    def fund(self, fund: Fund | str) -> QuerySet | None:
        if not fund:
            return self
        if isinstance(fund, str):
            try:
                fund = Fund.objects.get(fund=fund.upper())
            except Fund.DoesNotExist:
                return None
        return self.filter(fund=fund)

    def costcenter(self, costcenter: CostCenter | str) -> QuerySet | None:
        if not costcenter:
            return self
        if isinstance(costcenter, str):
            try:
                costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
            except CostCenter.DoesNotExist:
                return None
        return self.filter(costcenter=costcenter)

    def descendants_fundcenter(self, fundcenter: FundCenter | str) -> QuerySet | None:
        if not fundcenter:
            return self
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        fc_family = FundCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        return self.filter(fundcenter__in=fc_family)

    def descendants_costcenter(self, fundcenter: FundCenter | str) -> QuerySet | None:
        if not fundcenter:
            return self
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        cc_family = CostCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        return self.filter(costcenter__in=cc_family)

    def fundcenter(self, fundcenter: FundCenter | str) -> QuerySet | None:
        if not fundcenter:
            return self
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        return self.filter(fundcenter=fundcenter)

    def fy(self, fy: int) -> QuerySet | None:
        if not fy:
            return self
        return self.filter(fy=fy)

    def quarter(self, quarter: int) -> QuerySet | None:
        if not quarter:
            return self
        if str(quarter) not in QUARTERKEYS:
            return None
        return self.filter(quarter=quarter)


class Allocation(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fy = models.PositiveSmallIntegerField("Fiscal Year", choices=YEAR_CHOICES, default=datetime.now().year)
    quarter = models.CharField(max_length=1, choices=QUARTERS, default="0")
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    objects = AllocationQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.fund} - {self.amount}"

    def save(self, *args, **kwargs):
        if str(self.quarter) not in list(zip(*QUARTERS))[0]:
            raise exceptions.InvalidOptionException(
                f"Quarter {self.quarter} invalid.  Must be one of {','.join([x[0] for x in QUARTERS])}"
            )
        if self.amount < 0:
            raise exceptions.InvalidAllocationException("Allocation less than 0 is invalid")
        if self.fy not in [v[0] for v in YEAR_CHOICES]:
            raise exceptions.InvalidFiscalYearException(
                f"Fiscal year {self.fy} invalid, must be one of {','.join([v[1] for v in YEAR_CHOICES])}"
            )
        if not self.fund:
            raise ValueError("Allocation cannot be saved without Fund")
        super().save(*args, **kwargs)


class CostCenterAllocation(Allocation):
    costcenter = models.ForeignKey(
        CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center"
    )

    def __str__(self):
        return f"{self.costcenter} - {self.fund} - {self.fy} Q{self.quarter} {self.amount}"

    def save(self, *args, **kwargs):
        if not self.costcenter:
            raise ValueError(f"Allocation cannot be saved without Cost Center {self}")
        super(CostCenterAllocation, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Cost Center Allocations"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "costcenter",
                    "quarter",
                    "fy",
                ),
                name="unique_cost_center_allocation",
            )
        ]


class FundCenterAllocation(Allocation):
    fundcenter = models.ForeignKey(
        FundCenter, on_delete=models.CASCADE, null=True, verbose_name="Fund Center"
    )

    def __str__(self):
        return f"{self.fundcenter} - {self.fund} - {self.fy}Q{self.quarter} {self.amount}"

    class Meta:
        verbose_name_plural = "Fund Center Allocations"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "fundcenter",
                    "quarter",
                    "fy",
                ),
                name="unique_fund_center_allocation",
            )
        ]


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
