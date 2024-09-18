import csv
import logging
from datetime import datetime

import numpy as np
import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, models
from django.db.models import F, QuerySet, Sum, Value
from django.forms.models import model_to_dict
from pandas.io.formats.style import Styler

from bft import conf, exceptions
from bft.conf import PERIODS, QUARTERKEYS, QUARTERS, STATUS, YEAR_CHOICES
from main.settings import UPLOADS
from utils.dataframe import BFTDataFrame

np.set_printoptions(suppress=True)
logger = logging.getLogger("uploadcsv")


class BftStatusManager(models.Manager):
    """A class to access current fiscal year, quarter and period"""
    def fy(self) -> str | None:
        try:
            return BftStatus.objects.get(status="FY").value
        except BftStatus.DoesNotExist:
            return None

    def quarter(self) -> str | None:
        try:
            return BftStatus.objects.get(status="QUARTER").value
        except BftStatus.DoesNotExist:
            return None

    def period(self) -> str | None:
        try:
            return BftStatus.objects.get(status="PERIOD").value
        except BftStatus.DoesNotExist:
            return None


class BftStatus(models.Model):
    """A class to assign key-value applicable to the BFT.  Typical and mandatory keys are fiscal year, quarter and period."""
    status = models.CharField("Status", max_length=30, unique=True, choices=STATUS)
    value = models.CharField("Value", max_length=30)

    def __str__(self) -> str:
        return f"{self.status}:{self.value}"

    def save(self, *args, **kwargs):
        status, _ = zip(*STATUS)
        period_ids, _ = zip(*PERIODS)
        quarter_ids, _ = zip(*QUARTERS)

        if self.status not in status:
            raise AttributeError(f"{self.status} not a valid status. Expected value is one of  {status}")

        if self.status == "QUARTER" and self.value not in quarter_ids:
            raise ValueError(
                f"{self.value} is not a valid period.  Expected value is one of {(', ').join(map(str,quarter_ids))}"
            )

        if self.status == "PERIOD" and not conf.is_period(self.value):
            raise ValueError(
                f"{self.value} is not a valid period.  Expected value is one of {(', ').join(map(str,period_ids))}"
            )
        super(BftStatus, self).save(*args, **kwargs)

    objects = models.Manager()
    current = BftStatusManager()


class BftUserManager(BaseUserManager):
    """
    Bft user model manager where usernane is the unique identifiers and is derived from the email address
    for authentication.  email address domain must be @forces.gc.ca
    """

    @classmethod
    def normalize_user(cls, obj: "BftUser"):
        """A class method to make upper case the first letter of both first and last name from the BFTUser"""
        obj.first_name = obj.first_name.capitalize()
        obj.last_name = obj.last_name.capitalize()
        return obj

    @classmethod
    def make_username(cls, email) -> str:
        """Create username by extracting the username part of the email address

        Args:
            email (_type_): Email address
        Returns:
            str: Username
        """
        username, _ = email.strip().rsplit("@", 1)
        return username.lower()

    @classmethod
    def normalize_email(cls, email):
        """
        Normalize the email address by lowercasing both the domain and username part of the email address.  No need to call super()
        """
        email = email or ""
        try:
            email_name, domain_part = email.strip().rsplit("@", 1)
        except ValueError:
            pass
        else:
            email_name = email_name.lower()
            domain_part = domain_part.lower()
            email = email_name + "@" + domain_part

        if domain_part != "forces.gc.ca":
            raise ValueError("Domain Part of email not valid.  Expected forces.gc.ca")
        return email

    def create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_("The Email must be set"))  # noqa
        email = self.normalize_email(email)
        username, _ = email.strip().rsplit("@", 1)  # noqa
        user_model = get_user_model()
        user = user_model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))  # noqa
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))  # noqa
        try:
            extra_fields.pop("username")
        except Exception:
            pass
        return self.create_user(email, password, **extra_fields)


class BftUser(AbstractUser):
    """A class that extends AbstractUser base class.  The model has additional fields to satisfy the BFT needs"""
    default_fc = models.OneToOneField(
        "FundCenter",
        on_delete=models.RESTRICT,
        verbose_name="Default FC",
        blank=True,
        null=True,
    )
    default_cc = models.OneToOneField(
        "CostCenter",
        on_delete=models.RESTRICT,
        verbose_name="Default CC",
        blank=True,
        null=True,
    )
    procurement_officer = models.BooleanField(default=False)
    objects = BftUserManager()

    class Meta:
        permissions = (
            ("create_data", "can create data"),
            ("upload_data", "can upload data"),
        )


class BookmarkQuerySet(models.QuerySet):
    """A database lookup class for bookmark object"""
    def owner(self, owner: BftUser | str) -> QuerySet | None:
        """Get the bookmarks for the specified user."""
        if not owner:
            return self
        if isinstance(owner, str):
            try:
                owner = BftUser.objects.get(username=owner)
            except owner.DoesNotExist:
                return None
        return self.filter(owner=owner)

    def user_bookmark(self, request):
        """Get the bookmarks for the current user."""
        try:
            owner = BftUser.objects.get(username=request.user)
            bm = Bookmark.objects.filter(owner=owner)
        except BftUser.DoesNotExist:
            bm = None
        return bm


class Bookmark(models.Model):
    """Class model that describes the bookmarks assigned to BFT users."""
    owner = models.ForeignKey(BftUser, on_delete=models.CASCADE, default="", verbose_name="Owner's Favorite")
    bookmark_name = models.CharField(max_length=30)
    bookmark_link = models.CharField(max_length=125)
    bookmark_query_string = models.CharField(max_length=255, null=True)
    objects = models.Manager()
    search = BookmarkQuerySet.as_manager()

    def __str__(self):
        return f"{self.owner} - {self.bookmark_name} - {self.bookmark_link}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "bookmark_link",
                    "bookmark_query_string",
                    "owner",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]


class FundManager(models.Manager):
    """A manager for Fund object"""
    def fund(self, fund: str):
        """Get a fund object given the fund string"""
        try:
            obj = Fund.objects.get(fund__iexact=fund)
        except Fund.DoesNotExist:
            return None
        return obj

    def pk(self, pk: int):
        """Get a fund object given the primary key"""
        try:
            obj = Fund.objects.get(pk=pk)
        except Fund.DoesNotExist:
            return None
        return obj

    def exists(self, fund: str) -> bool:
        """Check the existance of a fund given the string"""
        return Fund.objects.filter(fund=fund).exists()

    def get_request(self, request) -> str | None:
        """Handle get request for fund specified in request"""
        fund = request.GET.get("fund")
        if fund:
            fund = fund.upper()
            if not FundManager().exists(fund):
                messages.info(request, f"Fund {fund} does not exist.")
                return ""
            return fund
        else:
            return None


class Fund(models.Model):
    """This model represents a fund such as C113, C523, etc.  The download field indicates if line items matching
    field should be downloaded during DRMIS download process.  When False, line item will be skipped.BB"""
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
        if not self.source.isupper():
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

    def get_sub_alloc(
        self, parent_alloc: "FundCenterAllocation"
    ) -> "FundCenterAllocation":
        seq = [
            s["sequence"] for s in self.get_direct_descendants(parent_alloc.fundcenter)
        ]
        dd = FundCenter.objects.filter(sequence__in=seq)
        return FundCenterAllocation.objects.filter(
            fundcenter__in=dd,
            fy=parent_alloc.fy,
            fund=parent_alloc.fund,
            quarter=parent_alloc.quarter,
        )

    def sequence_exist(self, sequence):
        return FundCenter.objects.filter(sequence=sequence).exists()

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
        data = (
            FundCenterAllocation.objects.fundcenter(fundcenter)
            .fund(fund)
            .fy(fy)
            .quarter(quarter)
        )
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

    def get_direct_descendants_dataframe(
        self, fundcenter: "FundCenter|str"
    ) -> list | None:
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

    def exists(self, fundcenter: str = None) -> bool:
        if fundcenter:
            return FundCenter.objects.filter(fundcenter=fundcenter.upper()).exists()
        else:
            return FundCenter.objects.count() > 0

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
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return self.has_cost_centers(fundcenter) + self.has_fund_centers(fundcenter)

    def has_fund_centers(self, fundcenter: "FundCenter|str") -> int:
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return FundCenter.objects.filter(fundcenter_parent=fundcenter).count()

    def has_cost_centers(self, fundcenter: "FundCenter|str") -> int:
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return CostCenter.objects.filter(costcenter_parent=fundcenter).count()

    def is_child_of(
        self, parent: "FundCenter", child: "FundCenter | CostCenter"
    ) -> bool:
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

    def is_descendant_of(
        self, parent: "FundCenter", child: "FundCenter | CostCenter"
    ) -> bool:
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

    def set_parent(
        self, fundcenter_parent: "FundCenter" = None, costcenter_child: bool = False
    ) -> str:
        """
        Create a sequence number by refering to the sequence numbers of the family of fundcenter_parent.
        The sequence number created contains the parent sequence plus the portion of the child.

        Args:
            fundcenter_parent (FundCenter, optional): The fund center that is the parent of the sub center that need a sequence number. Defaults to None.
            costcenter_child (bool, optional): If parent is for cost center, costcenter_child must be True. This will affect the way the sequence number is created. Defaults to False.

        Returns:
            str: A string the represents the child sequence number.
        """
        if fundcenter_parent is None:
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
            right_on=[
                "Costcenter_parent_ID",
                "FC Path",
                "Fund Center",
                "Fund Center Name",
            ],
        )
        merged = merged.fillna("")
        merged.set_index(
            [
                "FC Path",
                "Fund Center",
                "Fund Center Name",
                "Cost Center",
                "Cost Center Name",
            ],
            inplace=True,
        )
        merged.drop(
            [
                "Fundcenter_ID_x",
                "Fundcenter_ID_y",
                "Fundcenter_parent_ID_x",
                "Fundcenter_parent_ID_y",
                "Costcenter_ID",
                "CC Path",
                "Fund_ID",
                "Source_ID",
                "Costcenter_parent_ID",
                "Level_y",
                "first name",
                "last name",
                "superuser status",
                "Password",
                "active",
                "date joined",
                "active",
                "email address",
                "staff status",
                "Default_fc_ID",
                "Default_cc_ID",
                "Bftuser_ID",
                "last login",
                "procurement officer",
                "Procurement_officer_ID",
            ],
            axis=1,
            inplace=True,
        )
        merged.sort_values(by=["FC Path"], inplace=True)
        merged.rename(columns={"Level_x": "Level", "Username": "Procurement Officer"}, inplace=True)
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

    def CostCenters(self, fundcenter: "str|FundCenter"):
        if isinstance(fundcenter, str):
            fundcenter = FundCenterManager().fundcenter(fundcenter)
        if fundcenter:
            return CostCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        return None

    def all(self):
        pass


class FundCenter(models.Model):
    fundcenter = models.CharField("Fund Center", max_length=6, unique=True)
    shortname = models.CharField(
        "Fund Center Name", max_length=25, null=True, blank=True
    )
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
        if self.fundcenter_parent is None:
            self.sequence = FinancialStructureManager().new_root()
        elif (
            self.fundcenter_parent
            and self.fundcenter == self.fundcenter_parent.fundcenter
        ):
            raise IntegrityError("Children Fund center cannot assign itself as parent")
        elif not FinancialStructureManager().is_child_of(self.fundcenter_parent, self):
            self.sequence = FinancialStructureManager().set_parent(
                self.fundcenter_parent
            )

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

    def is_updatable(self, cc: "str|CostCenter") -> bool:
        if isinstance(cc, str):
            cc_: CostCenter = self.cost_center(cc)
            if cc_:
                return cc_.isupdatable
        elif isinstance(cc, CostCenter):
            return cc.isupdatable
        raise TypeError("Cost center of invalid type.")

    def has_line_items(self, costcenter: "CostCenter"):

        return LineItem.objects.filter(costcenter=costcenter).exists()

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
        proco_df = BFTDataFrame(BftUser).build(BftUser.objects.filter(procurement_officer=True))
        df = pd.merge(
            df,
            fc_df,
            how="left",
            left_on="Costcenter_parent_ID",
            right_on="Fundcenter_ID",
        )
        if not proco_df.empty:
            df = pd.merge(df, proco_df, how="left", left_on="Procurement_officer_ID", right_on="Bftuser_ID")
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
        data = (
            CostCenterAllocation.objects.costcenter(costcenter)
            .fund(fund)
            .fy(fy)
            .quarter(quarter)
        )
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
        if isinstance(parent, str):
            parent = FundCenterManager().fundcenter(fundcenter=parent)
        return CostCenter.objects.filter(costcenter_parent=parent)

    def exists(self, costcenter: str = None) -> bool:
        if costcenter:
            return CostCenter.objects.filter(costcenter=costcenter).exists()
        else:
            return CostCenter.objects.count() > 0

    def get_request(self, request) -> str | None:
        """Extract the cost center string from the request and verifies that it does exist."""
        costcenter = request.GET.get("costcenter")
        if costcenter:
            costcenter = costcenter.upper()
            if not CostCenterManager().exists(costcenter):
                messages.info(request, f"Cost Center {costcenter} does not exist.")
                return ""
            return costcenter
        else:
            return None


class CostCenter(models.Model):
    costcenter = models.CharField("Cost Center", max_length=6, unique=True)
    shortname = models.CharField(
        "Cost Center Name", max_length=35, blank=True, null=True
    )
    fund = models.ForeignKey(
        Fund, on_delete=models.RESTRICT, default="", verbose_name="Fund"
    )
    source = models.ForeignKey(
        Source, on_delete=models.RESTRICT, default="", verbose_name="Source"
    )
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
        indexes = [models.Index(fields=["costcenter"])]

    def save(self, *args, **kwargs):
        if not FinancialStructureManager().is_child_of(self.costcenter_parent, self):
            self.sequence = FinancialStructureManager().set_parent(
                self.costcenter_parent, costcenter_child=True
            )

        self.costcenter = self.costcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        super(CostCenter, self).save(*args, **kwargs)


class CapitalProjectManager(models.Manager):
    def project(self, capital_project: str) -> "CapitalProject | None":
        capital_project = capital_project.upper()
        try:
            obj = CapitalProject.objects.get(project_no__iexact=capital_project)
        except CapitalProject.DoesNotExist:
            return None
        return obj

    def exists(self, capital_project: str = None) -> bool:
        if capital_project:
            return CapitalProject.objects.filter(
                project_no=capital_project.upper()
            ).exists()
        else:
            return CapitalProject.objects.count() > 0

    def get_request(self, request) -> str | None:
        capital_project = request.GET.get("capital_project")
        if capital_project:
            capital_project = capital_project.upper()
            if not CapitalProjectManager().exists(capital_project):
                messages.info(
                    request, f"Capital Project {capital_project} does not exist."
                )
            return capital_project
        else:
            return None


class CapitalProject(models.Model):
    project_no = models.CharField("Project No", max_length=8, unique=True)
    shortname = models.CharField("Project Name", max_length=35, blank=True)
    isupdatable = models.BooleanField("Is Updatable", default=False)
    note = models.TextField(null=True, blank=True)
    # sequence = models.CharField("CC Path", max_length=25, unique=True, default="")
    fundcenter = models.ForeignKey(
        FundCenter,
        on_delete=models.RESTRICT,
        default="0",
        related_name="capital_projects",
        verbose_name="Fund Center",
    )
    procurement_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        limit_choices_to={"procurement_officer": True},
    )
    objects = CapitalProjectManager()

    def __str__(self):
        return f"{self.project_no.upper()} - {self.shortname}"

    class Meta:
        ordering = ["project_no"]
        verbose_name_plural = "Capital Projects"

    def save(self, *args, **kwargs):
        # if not FinancialStructureManager().is_child_of(self.fundcenter, self):
        # self.sequence = FinancialStructureManager().set_parent(self.fundcenter, costcenter_child=True)

        self.project_no = self.project_no.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        super(CapitalProject, self).save(*args, **kwargs)


class CapitalForecasting(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    fy = models.PositiveSmallIntegerField(
        "Fiscal Year", choices=YEAR_CHOICES, default=datetime.now().year
    )
    capital_project = models.ForeignKey(
        CapitalProject,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Capital Project",
    )
    commit_item = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "capital_project",
                    "commit_item",
                    "fy",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]

    def __str__(self):
        return f"{self.capital_project} - {self.fy} - {self.fund.fund}"

    def save(self, *args, **kwargs):
        if self.fy not in [v[0] for v in YEAR_CHOICES]:
            raise exceptions.InvalidFiscalYearException(
                f"Fiscal year {self.fy} invalid, must be one of {','.join([v[1] for v in YEAR_CHOICES])}"
            )
        if not self.fund:
            raise ValueError("Allocation cannot be saved without Fund")
        super().save(*args, **kwargs)


class CapitalYearEnd(CapitalForecasting):
    ye_spent = models.PositiveIntegerField(default=0)


class CapitalNewYear(CapitalForecasting):
    initial_allocation = models.PositiveIntegerField("Initial allocation", default=0)


class CapitalInYear(CapitalForecasting):
    quarter = models.CharField(max_length=1, choices=QUARTERS, default="0")
    allocation = models.PositiveIntegerField(default=0)
    spent = models.PositiveIntegerField(default=0)
    co = models.PositiveIntegerField(default=0)
    pc = models.PositiveIntegerField(default=0)
    fr = models.PositiveIntegerField(default=0)
    le = models.PositiveIntegerField(default=0)
    mle = models.PositiveIntegerField(default=0)
    he = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "capital_project",
                    "commit_item",
                    "fy",
                    "quarter",
                ),
                name="capital_in_year_is_unique",
            )
        ]


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
        if cc:
            fcst_adj = ForecastAdjustment.objects.filter(costcenter__in=cc)
            if fund:
                fund = FundManager().fund(fund)
                fcst_adj = fcst_adj.filter(fund=fund)
            lst = []
            d = {}
            for item in fcst_adj:
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
                lst.append(d)

        return lst


class ForecastAdjustment(models.Model):
    costcenter = models.ForeignKey(
        CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center"
    )
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT
    )
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.costcenter} - {self.fund} - {self.amount}"

    class Meta:
        ordering = ["costcenter", "fund"]
        verbose_name_plural = "Forecast Adjustments"

    def save(self, *args, **kwargs):
        if not CostCenterManager().has_line_items(self.costcenter):
            raise exceptions.LineItemsDoNotExistError(
                f"{self.costcenter} has no line items.  Forecast adjustment rejected."
            )

        super().save(*args, **kwargs)


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
    fy = models.PositiveSmallIntegerField(
        "Fiscal Year", choices=YEAR_CHOICES, default=datetime.now().year
    )
    quarter = models.CharField(max_length=1, choices=QUARTERS, default="0")
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT
    )
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
            raise exceptions.InvalidAllocationException(
                "Allocation less than 0 is invalid"
            )
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
        return (
            f"{self.costcenter} - {self.fund} - {self.fy} Q{self.quarter} {self.amount}"
        )

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
        return (
            f"{self.fundcenter} - {self.fund} - {self.fy}Q{self.quarter} {self.amount}"
        )

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


class LineItemManager(models.Manager):
    def cost_center(self, costcenter: str):
        costcenter = costcenter.upper()
        try:
            cc = CostCenter.objects.get(costcenter=costcenter)
        except CostCenter.DoesNotExist:
            return None
        return self.filter(costcenter=cc)

    def has_line_items(self, costcenter: "CostCenter") -> bool:
        return LineItem.objects.filter(costcenter=costcenter).exists()

    def line_item_dataframe(
        self, fund: str = None, doctype: str = None
    ) -> pd.DataFrame:
        """Prepare a pandas dataframe of the DRMIS line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of DRMIS line items
        """
        data = LineItem.objects.all()
        if fund:
            data = data.filter(fund=fund.upper())
        if doctype:
            data = data.filter(doctype=doctype.upper())
        if data:
            df = BFTDataFrame(LineItem).build(data)
            df["CO"] = np.where(df["Doctype"] == "CO", df["Balance"], 0)
            df["PC"] = np.where(df["Doctype"] == "PC", df["Balance"], 0)
            df["FR"] = np.where(df["Doctype"] == "FR", df["Balance"], 0)
            return df
        else:
            return pd.DataFrame({})

    def line_item_detailed_dataframe(self, fund=None, doctype=None) -> pd.DataFrame:
        """
        Prepare a pandas dataframe of merged line items, forecast line items and cost center.

        Returns:
            pd.DataFrame : A dataframe of line items including forecast.
        """
        li_df = self.line_item_dataframe(fund=fund, doctype=doctype)
        if li_df.empty:
            return li_df
        if len(li_df) > 0:
            fcst_df = LineForecastManager().forecast_dataframe()
            cc_df = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())

            if len(fcst_df) > 0:
                li_df = pd.merge(li_df, fcst_df, how="left", on="Lineitem_ID").fillna(0)
                li_df["Forecast"] = li_df["Forecast"].astype("int")
            else:
                li_df["Forecast"] = 0
            li_df = pd.merge(li_df, cc_df, how="left", on="Costcenter_ID")

        return li_df


class LineItem(models.Model):
    docno = models.CharField(max_length=10)
    lineno = models.CharField(max_length=7)  # lineno : acctassno
    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fundcenter = models.CharField(max_length=6)
    fund = models.CharField(max_length=4)
    costcenter = models.ForeignKey(CostCenter, on_delete=models.RESTRICT)
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
    status = models.CharField(max_length=10, null=True, blank=True, default="")
    fcintegrity = models.BooleanField(default=False)

    # lineitem = models.Manager()
    objects = LineItemManager()

    def __str__(self):
        text = f"{self.enctype} {self.docno}-{self.lineno}"
        return str(text)

    class Meta:
        ordering = ["-docno", "lineno"]
        verbose_name_plural = "Line Items"

    def get_orphan_lines(self, costcenter: str | CostCenter = None):
        """
        Compare the docno and lineno combination in both line item table and
        encumbrance table.  When specifying costcenter, only the lines of the specified cost center will be considered.
        """
        if costcenter:
            if isinstance(costcenter, str):
                try:
                    costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
                except CostCenter.DoesNotExist:
                    return None
            lines = set(
                LineItem.objects.filter(costcenter=costcenter).values_list(
                    "docno", "lineno"
                )
            )
        else:
            lines = set(LineItem.objects.values_list("docno", "lineno"))

        enc = set(LineItemImport.objects.values_list("docno", "lineno"))
        orphans = lines.difference(enc)

        if costcenter:
            logger.info(
                f"Found {len(orphans)} orphan lines for cost center {costcenter}."
            )
        else:
            logger.info(
                f"Found {len(orphans)} orphan lines considering all cost centers."
            )

        return orphans

    def mark_orphan_lines(self, orphans: set):
        """Set the status of the line item to orphan.  Because these lines are orphans, their forecast amount is also set to 0 leaving comments and description unaffected.

        Args:
            orphans (set): Lines that need to have their status updated to orphan.
        """
        logger.info("Begin marking orphan lines")
        for o in orphans:
            docno, lineno = o
            try:
                li = LineItem.objects.get(docno=docno, lineno=lineno)
                li.spent = 0
                li.workingplan = 0
                li.balance = 0
                li.status = "orphan"
                li.save()
            except LineItem.DoesNotExist:
                logger.info(f"LineItem {docno} - {lineno} does not exist")
        LineForecast.objects.filter(lineitem__status="orphan").update(forecastamount=0)

    def insert_line_item(self, ei: "LineItemImport"):
        """
        Insert the encumbrance line in line item table.  Such line is set as new in the
        status field.
        """
        cc = CostCenter.objects.get(costcenter=ei.costcenter)
        di = model_to_dict(ei)
        di["costcenter"] = cc
        del di["id"]
        target = LineItem(**di)
        target.status = "New"
        target.save()
        return target.id

    def update_line_item(self, li: "LineItem", ei: "LineItemImport"):
        """
        Update line items fields using values from encumbrance line.
        """
        cc = None
        try:
            cc = CostCenter.objects.get(costcenter=ei.costcenter)
        except CostCenter.DoesNotExist:
            pass  # for now.

        if cc:
            li.costcenter = cc
            li.fundcenter = ei.fundcenter
            li.spent = ei.spent
            li.workingplan = ei.workingplan
            li.balance = ei.balance
            li.fund = ei.fund
            li.status = "Updated"
            # TODO More to come
            li.save()
            return li
        else:
            return None

    def import_lines(self):
        """
        import_line function relies on content of encumbrance_import.  It is
        responsible to import new lines, update current ones and zero out lines
        no longer in DRMIS
        """

        count = LineItem.objects.all().update(status="old")
        logger.info(f"Set {count} lines to old.")

        cc_no_update = CostCenter.objects.filter(isupdatable=False).values_list("costcenter", flat=True)
        encumbrance = LineItemImport.objects.all()
        logger.info(f"Retreived {encumbrance.count()} encumbrance lines.")
        for e in encumbrance:
            if e.costcenter in cc_no_update:
                continue
            try:
                target = LineItem.objects.get(docno=e.docno, lineno=e.lineno)
                self.update_line_item(target, e)
            except LineItem.DoesNotExist:
                self.insert_line_item(e)

    def set_fund_center_integrity(self):
        """
        Compare all line items cost center - fund center pair with
        cost center - fund center pair from cost center table.  When comparison
        match for a given line, set its fcintegrity to True.  All fcintegrity are
        set to False to start with.
        """
        logger.info("Fund center integrity check begins.")
        cc = CostCenter.objects.select_related()
        cc_set = set()
        for c in cc:
            cc_set.add((c.costcenter, c.costcenter_parent.fundcenter))

        li = LineItem.objects.select_related()
        li.update(fcintegrity=False)

        for item in li:
            t = (item.costcenter.costcenter, item.fundcenter)
            if t in cc_set:
                item.fcintegrity = True
                item.save()
        logger.info("Fund center integrity check completed.")

    def set_doctype(self):
        logger.info("Set doctype begins")
        types = [
            {"enctype": "Funds Commitment", "doctype": "CO"},
            {"enctype": "Funds Precommitment", "doctype": "PC"},
            {"enctype": "Funds Reservation", "doctype": "FR"},
            {"enctype": "Purchase Order", "doctype": "CO"},
            {"enctype": "Purchase Requisitions", "doctype": "PC"},
        ]
        for t in types:
            li = LineItem.objects.filter(enctype=t["enctype"]).update(
                doctype=t["doctype"]
            )
            logger.info(f"Set {li} lines to {t['doctype']}")
        logger.info("Set doctype complete")


class LineForecastManager(models.Manager):
    def get_line_forecast(self, lineitem: LineItem) -> "LineForecast | None":
        if hasattr(lineitem, "fcst"):
            return LineForecast.objects.get(lineitem_id=lineitem.id)
        else:
            return None

    def forecast_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the forecast line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of forecast lines
        """
        if not LineForecast.objects.exists():
            return pd.DataFrame()
        data = LineForecast.objects.all()
        df = BFTDataFrame(LineForecast).build(data)
        return df

    def update_owner(
        self, costcenter: CostCenter, new_owner: BftUser, old_owner: BftUser = None
    ) -> int:
        """This function allows for transfer ownership of forecasted lines for a given cost center and optionally the loosing owner.

        Args:
            costcenter (CostCenter): Cost center of choice for which lines will be moved
            new_owner (BftUser): Bft User that will be assigned the lines.
            old_owner (BftUser, optional): Bft User whose lines will be transfered. Defaults to None.. Defaults to None.

        Returns:
            int: Number of lines transfered.
        """

        lines = LineForecast.objects.filter(lineitem__costcenter=costcenter)
        if lines:
            return lines.update(owner=new_owner)

    def set_underforecasted(self, costcenter: CostCenter = None) -> int:
        """Adjust the forecast of line items to match the spent if the forecast is lower than the spent"""
        lines = LineForecast.objects.filter(lineitem__spent__gt=F("forecastamount"))
        if costcenter:
            lines = lines.filter(lineitem__costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} lines with spent greater than forecast.")
        for li in lines:
            li.forecastamount = li.lineitem.spent
        affected = LineForecast.objects.bulk_update(lines, ["forecastamount"])
        logger.info(f"Forecasted to spent {affected} out of {maxlines} lines")
        return affected

    def set_overforecasted(self, costcenter: CostCenter | str = None) -> int:
        """Adjust the forecast of line items to match the working plan if the forecast is highr than the working plan"""
        lines = LineForecast.objects.filter(
            lineitem__workingplan__lt=F("forecastamount")
        )
        if costcenter:
            lines = lines.filter(lineitem__costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} lines with working plan less than forecast.")
        for li in lines:
            li.forecastamount = li.lineitem.workingplan
        affected = LineForecast.objects.bulk_update(lines, ["forecastamount"])
        logger.info(f"Forecasted to working plan {affected} out of {maxlines} lines")
        return affected

    def set_encumbrance_history_record(self, costcenter: CostCenter = None) -> int:
        """Primarily used during line import, set the working plans, spent and balance values in the LineForecast model for historical purpose.  These will remain uneditable.

        Returns:
            int: Number of lines affected.
        """
        lines = LineItem.objects.filter(status="New")
        if costcenter:
            lines = lines.filter(costcenter=costcenter)
        maxlines = lines.count()
        logger.info(f"{maxlines} new lines need encumbrance record history to be set.")
        counter = 0
        li: LineItem
        for li in lines:
            if not li.costcenter.isforecastable:
                continue
            counter += 1
            li_fcst = LineForecast(
                lineitem=li,
                spent_initial=li.spent,
                workingplan_initial=li.workingplan,
                balance_initial=li.balance,
            )
            li_fcst.save()
        if counter == maxlines:
            logger.info(f"Encumbrance history set for {counter} out of {maxlines}")
        else:
            logger.warn(f"Encumbrance history set for {counter} out of {maxlines}")
        return counter


class LineForecast(models.Model):
    forecastamount = models.DecimalField(
        "Forecast", max_digits=10, decimal_places=2, default=0
    )
    spent_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_initial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    workingplan_initial = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    description = models.CharField(max_length=512, null=True, blank=True)
    comment = models.CharField(max_length=512, null=True, blank=True)
    deliverydate = models.DateField("Delivery Date", null=True, blank=True)
    delivered = models.BooleanField(default=False)
    lineitem = models.OneToOneField(
        LineItem, on_delete=models.SET_NULL, related_name="fcst", null=True
    )
    buyer = models.CharField(max_length=175, null=True, blank=True)  # PWGSC buyer
    owner = models.ForeignKey(
        BftUser,
        on_delete=models.RESTRICT,
        default="",
        null=True,
        limit_choices_to={"procurement_officer": True},
    )
    updated = models.DateTimeField(auto_now=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        text = ""
        if self.lineitem:
            text = f"{self.forecastamount} - {self.id} -  {self.lineitem.id}"
        return str(text)

    def save(self, *args, **kwargs):
        if not self.forecastable():
            self.forecastamount = self.lineitem.fcst.forecastamount
        if self.forecastamount > self.lineitem.workingplan:
            self.forecastamount = self.lineitem.workingplan
        if self.forecastamount < self.lineitem.spent:
            self.forecastamount = self.lineitem.spent
        super(LineForecast, self).save(*args, **kwargs)

    def forecastable(self) -> bool:
        return self.lineitem.costcenter.isforecastable

    def below_spent(self, request, lineitem: LineItem) -> bool:
        if self.forecastamount < lineitem.spent:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be smaller than spent {lineitem.spent}",
            )
            return True
        return False

    def above_working_plan(self, request, lineitem: LineItem) -> bool:
        if self.forecastamount > lineitem.workingplan:
            messages.warning(
                request,
                f"Forecast {self.forecastamount} cannot be higher than working plan {lineitem.workingplan}",
            )
            return True
        return False

    def forecast_lines(self, lines: QuerySet[LineItem], ratio):
        for li in lines:
            if hasattr(li, "fcst"):
                li_fcst = LineForecastManager().get_line_forecast(li)
                li_fcst.forecastamount = float(li.workingplan) * ratio
                li_fcst.save()
            else:
                li_fcst = LineForecast(lineitem=li, forecastamount=float(li.workingplan) * ratio)
                li_fcst.save()

    def forecast_line_by_docno(self, docno: str, forecast: float) -> int:
        lines = LineItem.objects.filter(docno=docno)
        if not lines:
            return 0

        lines_with_spent = lines.filter(spent__gt=0)
        lines_no_spent = lines.filter(spent=0)

        full_working_plan = lines.aggregate(models.Sum("workingplan"))["workingplan__sum"]
        unspent_working_plan = lines_no_spent.aggregate(models.Sum("workingplan"))["workingplan__sum"]

        spent_ratio = float(forecast) / float(full_working_plan)
        spent_forecast = 0
        if lines_with_spent:
            self.forecast_lines(lines_with_spent, spent_ratio)
            spent_forecast = LineItem.objects.filter(docno=docno, spent__gt=0).aggregate(Sum("fcst__forecastamount"))[
                "fcst__forecastamount__sum"
            ]

        if unspent_working_plan:
            unspent_ratio = (float(forecast) - float(spent_forecast)) / float(unspent_working_plan)
            self.forecast_lines(lines_no_spent, unspent_ratio)
        return len(lines)

    def forecast_costcenter_lines(self, costcenter: str, forecast: float) -> int:
        costcenter = CostCenterManager().cost_center(costcenter)
        if not costcenter:
            return 0
        lines = LineItem.objects.filter(costcenter=costcenter)
        if not lines:
            return 0

        lines_with_spent = lines.filter(spent__gt=0)
        lines_no_spent = lines.filter(spent=0)

        full_working_plan = lines.aggregate(models.Sum("workingplan"))["workingplan__sum"]
        unspent_working_plan = lines_no_spent.aggregate(models.Sum("workingplan"))["workingplan__sum"]

        spent_ratio = float(forecast) / float(full_working_plan)
        spent_forecast = 0

        if lines_with_spent:
            self.forecast_lines(lines_with_spent, spent_ratio)
            spent_forecast = LineItem.objects.filter(costcenter=costcenter, spent__gt=0).aggregate(
                Sum("fcst__forecastamount")
            )["fcst__forecastamount__sum"]

        if unspent_working_plan:
            unspent_ratio = (float(forecast) - float(spent_forecast)) / float(unspent_working_plan)
            self.forecast_lines(lines_no_spent, unspent_ratio)

        return len(lines)


class LineItemImport(models.Model):
    """
    LineItemImport class defines the model that represents the DND cost
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

    def insert_current(self, fy, period) -> int:
        """Insert in the monthly cost center charges table lines taken from charges import.  Insert selection is executed based on the provided fy and period equals to or less than provided period.  This is to ensure there is a rollup of charges on a monthly basis.

        Returns:
            int: Number of lines inserted
        """
        current = (
            CostCenterChargeImport.objects.filter(fy=fy, period__lte=period)
            .values("costcenter", "fund", "fy")
            .annotate(amount=Sum("amount"), period=Value(period))
        )
        lines = CostCenterChargeMonthly.objects.bulk_create(
            [CostCenterChargeMonthly(**c) for c in current]
        )
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
            engine="python",
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
        df.loc[df["ValCOArCur"].str.endswith("-"), "ValCOArCur"] = "-" + df[
            "ValCOArCur"
        ].str.replace("-", "")

        # set FY
        df["fy"] = self.fy

        # Confirm we have one single period
        periods = df["Per"].to_numpy()
        all_same = (periods[0] == periods).all()
        if not all_same:
            raise ValueError("element values in periods are not all the same")

        # Confirm period passed to command line matches those of csv file
        if periods[0] != period:
            raise ValueError(
                f"Requested period {period} does not match the periods in the file"
            )

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
