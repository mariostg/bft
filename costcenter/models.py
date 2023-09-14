from datetime import datetime
import numpy as np
from django.contrib import messages
from django.db import models, IntegrityError
from django.db.models import QuerySet
from django.conf import settings
from django.forms.models import model_to_dict
import pandas as pd
from bft.conf import YEAR_CHOICES, QUARTERS, QUARTERKEYS
from bft import exceptions
from utils.dataframe import BFTDataFrame


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

        df["Parent_ID"] = df["Parent_ID"].fillna(0).astype("int")
        return df

    def allocation(
        self,
        fundcenter: "FundCenter|str" = None,
        fund: Fund | str = None,
        fy: int = None,
        quarter: str = None,
        columns: list = None,
    ) -> "QuerySet | FundCenterAllocation":
        """This function retreive fund center allocation based on provided parameters.

        Args:
            fundcenter (FundCenter|str, optional): Fund Center of interest. Defaults to None.
            fund (str, optional): Fund of allocation. Defaults to None.
            fy (int, optional): Fiscal Year of interest. Defaults to None.
            quarter (str, optional): Quarter of interest. Defaults to None.
            columns (list, optional): List of columns names to include in the results.  Column must be valid field names from the model.

        Returns:
            QuerySet | FundCenterAllocation: If only one element is retreived, a FundCenterAllocation will be returned.  If more than one element is retreived, a QuerySet will be returned.  If not allocation is retreived, a FundCenterAllocation object will be returned and will contains the applicable parameters passed and an allocation of 0.
        """
        if columns:
            alloc = FundCenterAllocation.objects.all().values(*columns)
        else:
            alloc = FundCenterAllocation.objects.all()
        if fundcenter:
            if isinstance(fundcenter, str):
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            alloc = alloc.filter(fundcenter=fundcenter)
        if fund:
            if isinstance(fund, str):
                fund = FundManager().fund(fund)
            alloc = alloc.filter(fund=fund)
        if fy:
            alloc = alloc.filter(fy=fy)
        if str(quarter) in QUARTERKEYS:
            alloc = alloc.filter(quarter=quarter)

        rows = alloc.count()
        if not rows:
            return FundCenterAllocation(fundcenter=fundcenter, fund=fund, fy=fy, quarter=quarter, amount=0)
        elif rows == 1:
            return alloc[0]
        else:
            return alloc

    def allocation_dataframe(
        self, fundcenter: "FundCenter|str" = None, fund: "Fund|str" = None, fy: int = None, quarter: str = None
    ) -> pd.DataFrame:
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return pd.DataFrame()
        if isinstance(fund, str):
            try:
                fund = Fund.objects.get(fund=fund.upper())
            except Fund.DoesNotExist:
                return pd.DataFrame()
        columns = ["fundcenter__fundcenter", "fund__fund", "amount", "fy", "quarter"]
        data = self.allocation(fundcenter=fundcenter, fund=fund, fy=fy, quarter=quarter, columns=columns)
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

    def get_fund_centers(self, parent: "FundCenter") -> list:
        return list(FundCenter.objects.filter(parent=parent).values())

    def get_cost_centers(self, parent: "FundCenter") -> list:
        return list(CostCenter.objects.filter(parent=parent).values())

    def exists(self, fundcenter: str) -> bool:
        return FundCenter.objects.filter(fundcenter=fundcenter).exists()

    def get_request(self, request) -> str | None:
        fundcenter = request.GET.get("fundcenter")
        if fundcenter:
            fundcenter = fundcenter.upper()
            if not FundCenterManager().exists(fundcenter):
                messages.info(request, "Fund Center specified does not exist.")
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
        return FundCenter.objects.filter(parent=fundcenter).count()

    def has_cost_centers(self, fundcenter: "FundCenter|str") -> int:
        if type(fundcenter) == str:
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return CostCenter.objects.filter(parent=fundcenter).count()

    def is_child_of(self, parent: "FundCenter", child: "FundCenter | CostCenter") -> bool:
        """Check if child object is a direct descendant of parent

        Args:
            parent (FundCenter): A fund center object.
            child (FundCenter | CostCenter): A fund center or cost center object

        Returns:
            bool: True is child is direct descendant of parent.
        """
        return parent.fundcenter == child.parent.fundcenter

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
            return "1"
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
        cc = CostCenter.objects.filter(parent=fundcenter)
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
            family (list): A list of sequence no representing the members of the family 
            where the child will be added'
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

    def CostCenters(self):
        pass

    def all(self):
        pass


class FundCenter(models.Model):
    fundcenter = models.CharField("Fund Center", max_length=6, unique=True)
    shortname = models.CharField("Fund Center Name", max_length=25, null=True, blank=True)
    sequence = models.CharField("FC Sequence No", max_length=25, unique=True, default="1")
    parent = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="parent_fc",
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
        if self.sequence == None and self.parent == None:
            self.sequence = "1"
        if self.parent and self.fundcenter == self.parent.fundcenter:
            raise IntegrityError("Children Fund center cannot assign itself as parent")
        self.fundcenter = self.fundcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
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

    def get_sub_alloc(self, fc: FundCenter | str, fund: Fund | str, fy: int, quarter: int) -> "CostCenterAllocation":
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
        print(fc_df)
        df = pd.merge(df, fc_df, how="left", left_on="Parent_ID", right_on="Fundcenter_ID")
        return df

    def allocation(
        self,
        costcenter: "CostCenter|str" = None,
        fund: Fund | str = None,
        fy: int = None,
        quarter: int = None,
    ) -> QuerySet:
        """This method returns a cost center allocation queryset based on the specified query parameters.

        Args:
            costcenter (CostCenter|str, optional): A Cost Center that exist in the system. Defaults to None.
            fund (Fund | str, optional): Fund assigned to the allocation. Defaults to None.
            fy (int, optional): Fiscal year applicable to the allocation. Defaults to None.
            quarter (int, optional): Quarter applicable to the allocation. Defaults to None.

        Returns:
            QuerySet: A queryset of one or more cost center allocations.
        """
        alloc = CostCenterAllocation.objects.all()
        if costcenter:
            if isinstance(costcenter, str):
                costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
            alloc = alloc.filter(costcenter=costcenter)
        if fund:
            if isinstance(fund, str):
                fund = Fund.objects.get(fund=fund.upper())
            alloc = alloc.filter(fund=fund)
        if fy:
            alloc = alloc.filter(fy=fy)
        if str(quarter) in QUARTERKEYS:
            alloc = alloc.filter(quarter=quarter)
        return alloc

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
        if isinstance(costcenter, str):
            try:
                costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
            except CostCenter.DoesNotExist:
                return pd.DataFrame()
        if isinstance(fund, str):
            try:
                fund = Fund.objects.get(fund=fund.upper())
            except Fund.DoesNotExist:
                return pd.DataFrame()

        data = list(
            self.allocation(costcenter=costcenter, fund=fund, fy=fy, quarter=quarter).values(
                "costcenter__parent__fundcenter",
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
            "costcenter__parent__fundcenter": "Fund Center",
            "fund__fund": "Fund",
        }
        df = pd.DataFrame(data).rename(columns=columns)
        return df

    def forecast_adjustment_dataframe(self) -> pd.DataFrame:
        if not ForecastAdjustment.objects.exists():
            return pd.DataFrame()
        data = list(
            ForecastAdjustment.objects.all().values(
                "costcenter__parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
            )
        )
        columns = {
            "amount": "Forecast Adjustment",
            "costcenter__parent__fundcenter": "Fund Center",
            "costcenter__costcenter": "Cost Center",
            "fund__fund": "Fund",
        }
        return pd.DataFrame(data).rename(columns=columns)

    def get_sibblings(self, parent: FundCenter | str):
        if type(parent) == str:
            parent = FundCenterManager().fundcenter(fundcenter=parent)
        return CostCenter.objects.filter(parent=parent)


class CostCenter(models.Model):
    costcenter = models.CharField("Cost Center", max_length=6, unique=True)
    shortname = models.CharField("Cost Center Name", max_length=35, blank=True, null=True)
    fund = models.ForeignKey(Fund, on_delete=models.RESTRICT, default="", verbose_name="Fund")
    source = models.ForeignKey(Source, on_delete=models.RESTRICT, default="", verbose_name="Source")
    isforecastable = models.BooleanField("Is Forecastable", default=False)
    isupdatable = models.BooleanField("Is Updatable", default=False)
    note = models.TextField(null=True, blank=True)
    sequence = models.CharField("CC Sequence No", max_length=25, unique=True, default="")
    parent = models.ForeignKey(
        FundCenter, on_delete=models.RESTRICT, default="0", related_name="children", verbose_name="Parent"
    )

    objects = CostCenterManager()

    def __str__(self):
        return f"{self.costcenter.upper()} - {self.shortname}"

    class Meta:
        ordering = ["costcenter"]
        verbose_name_plural = "Cost Centers"

    def save(self, *args, **kwargs):
        self.costcenter = self.costcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        super().save(*args, **kwargs)


class ForecastAdjustment(models.Model):
    costcenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center")
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


class Allocation(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fy = models.PositiveSmallIntegerField("Fiscal Year", choices=YEAR_CHOICES, default=datetime.now().year)
    quarter = models.CharField(max_length=1, choices=QUARTERS, default="0")
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

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
        return super().save(*args, **kwargs)


class CostCenterAllocation(Allocation):
    costcenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center")

    def __str__(self):
        return f"{self.costcenter} - {self.fund} - {self.fy} Q{self.quarter} {self.amount}"

    def save(self, *args, **kwargs):
        if not self.costcenter:
            raise ValueError("Allocation cannot be saved without Cost Center")
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
    fundcenter = models.ForeignKey(FundCenter, on_delete=models.CASCADE, null=True, verbose_name="Fund Center")

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
