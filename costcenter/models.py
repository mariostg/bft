from datetime import datetime
import numpy as np
from typing import Iterable, Optional
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings

from bft.conf import YEAR_CHOICES, QUARTERS
from bft import exceptions


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
    def fundcenter(self, fundcenter: str):
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

    def sequence_exist(self, sequence):
        return FundCenter.objects.filter(sequence=sequence).exists()

    def fund_center_exist(self, fc):
        return FundCenter.objects.filter(fundcenter=fc).exists()


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

    def sequence_exists(self, seqno=None, fundcenter=None) -> bool:
        if seqno:
            return seqno in [x.sequence for x in self.FundCenters(seqno=seqno)]

    def set_parent(self, fundcenter_parent: "FundCenter" = None) -> str:
        """
        Create a sequence number by refering to the sequence numbers of the family of fundcenter_parent.
        The sequence number created contains the parent sequence plus the portion of the child.

        Args:
            fundcenter_parent (FundCenter, optional): The fund center that is the parent of the sub center that need a sequence number. Defaults to None.

        Returns:
            str: A string the represents the child sequence number.
        """
        if fundcenter_parent == None:
            return "1"
        family = list(self.FundCenters(seqno=fundcenter_parent.sequence).values_list("sequence", flat=True))
        new_seq = self.create_child(family, fundcenter_parent.fundcenter)
        return new_seq

    def is_descendant_of_parent(self, parent, child) -> bool:
        if len(child) <= len(parent):
            return False
        for k, v in enumerate(parent):
            if child[k] == v:
                continue
            else:
                return False
        return True

    def is_child_of_parent(self, parent, child) -> bool:
        if len(child) - 2 != len(parent):
            return False

        return self.is_descendant_of_parent(parent, child)

    def get_descendants(self, family, parent) -> list:
        if parent not in family:
            raise exceptions.ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_descendant_of_parent(parent, d):
                descendants.append(d)
        return descendants

    def get_direct_descendants(self, family: list, parent: str) -> list:
        if parent not in family:
            raise exceptions.ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_child_of_parent(parent, d):
                descendants.append(d)
        return descendants

    def create_child(self, family: list, parent: str = None, seqno: str = None) -> str:
        from costcenter.models import FundCenterManager

        """Create a new sequence number to be attributed to a cost center or a fund center.
        Either parent or seqno is required, not both or Exception will be raised.

        Args:
            family (list): A list of sequence no representing the members of the family 
            where the child will be added'
            parent (str, optional): A string representing the parent Fund Center. 
            Defaults to None.
            seqno (str, optional): A string representing the sequence number to be givent to the child. 
            Defaults to None.

        Returns:
            str: The sequence number of the child.
        """
        if parent and seqno:
            raise exceptions.IncompatibleArgumentsError(fundcenter=parent, seqno=seqno)
        if parent:
            seqno = FundCenterManager().fundcenter(parent).sequence
        children = self.get_direct_descendants(family, seqno)
        if children == []:
            new_born = seqno + ".1"
            family.append(new_born)
            return new_born
        splitted = [i.split(".") for i in children]
        splitted = np.array(splitted).astype(int)
        oldest = list(splitted.max(axis=0))
        new_born = oldest
        new_born[-1] = int(new_born[-1]) + 1
        new_born = [str(i) for i in new_born]
        new_born = ".".join(new_born)
        family.append(new_born)
        return new_born

    def CostCenters(self):
        pass

    def all(self):
        pass


class FundCenter(models.Model):
    fundcenter = models.CharField("Fund Center", max_length=6, unique=True)
    shortname = models.CharField("Short Name", max_length=25, null=True, blank=True)
    sequence = models.CharField("Sequence No", max_length=25, null=True, unique=True)
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
    def cost_center(self, costcenter: str):
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


class CostCenter(models.Model):
    costcenter = models.CharField("Cost Center", max_length=6, unique=True)
    shortname = models.CharField("Short Name", max_length=35, blank=True, null=True)
    fund = models.ForeignKey(Fund, on_delete=models.RESTRICT, default="")
    source = models.ForeignKey(Source, on_delete=models.RESTRICT, default="")
    isforecastable = models.BooleanField("Is Forecastable", default=False)
    isupdatable = models.BooleanField("Is Updatable", default=False)
    note = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        FundCenter,
        on_delete=models.RESTRICT,
        default="0",
        related_name="children",
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
    quarter = models.TextField(max_length=2, choices=QUARTERS, default="Q0")
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.fund} - {self.amount}"

    def save(self):
        if self.quarter not in list(zip(*QUARTERS))[0]:
            raise exceptions.InvalidOptionException(
                f"Quarter {self.quarter} invalid.  Must be one of {','.join([x[0] for x in QUARTERS])}"
            )
        if self.amount < 0:
            raise exceptions.InvalidAllocationException("Allocation less than 0 is invalid")
        if self.fy not in [v[0] for v in YEAR_CHOICES]:
            raise exceptions.InvalidFiscalYearException(
                f"Fiscal year {self.fy} invalid, must be one of {','.join([v[1] for v in YEAR_CHOICES])}"
            )
        return super().save()


class CostCenterAllocation(Allocation):
    costcenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center")

    def __str__(self):
        return f"{self.costcenter} - {self.fund} - {self.fy}{self.quarter} {self.amount}"

    class Meta:
        verbose_name_plural = "Cost Center Allocations"
