from datetime import datetime
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


class FundCenter(models.Model):
    fundcenter = models.CharField(max_length=6, unique=True)
    shortname = models.CharField(max_length=25, null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="parent_fc",
    )

    def __str__(self):
        return f"{self.fundcenter.upper()} - {self.shortname.upper()}"

    class Meta:
        ordering = ["fundcenter"]
        verbose_name_plural = "Fund Centers"

    def validate_unique(self, exclude=None):
        qs = FundCenter.objects.filter(fundcenter=self.fundcenter).exists()
        if qs:
            raise ValidationError("Fund center must be unique.")

    def save(self, *args, **kwargs):
        if self.parent and self.fundcenter == self.parent.fundcenter:
            raise IntegrityError("Children Fund center cannot assign itself as parent")
        self.validate_unique()
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
    costcenter = models.CharField(max_length=6, unique=True)
    shortname = models.CharField(max_length=35, blank=True, null=True)
    fund = models.ForeignKey(Fund, on_delete=models.RESTRICT, default="")
    source = models.ForeignKey(Source, on_delete=models.RESTRICT, default="")
    isforecastable = models.BooleanField(default=False)
    isupdatable = models.BooleanField(default=False)
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
        self.shortname = self.shortname.upper()
        super().save(*args, **kwargs)


class ForecastAdjustment(models.Model):
    costcenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True)
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
    fy = models.PositiveSmallIntegerField(choices=YEAR_CHOICES, default=datetime.now().year)
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
    costcenter = models.ForeignKey(CostCenter, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.costcenter} - {self.fund} - {self.fy}{self.quarter} {self.amount}"

    class Meta:
        verbose_name_plural = "Cost Center Allocations"
