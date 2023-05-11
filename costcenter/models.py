from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings


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


class Source(models.Model):
    source = models.CharField(max_length=24)

    def __str__(self):
        return f"{self.source}"

    class Meta:
        verbose_name_plural = "Sources"

    def save(self, *args, **kwargs):
        self.source = self.source.capitalize()
        super(Source, self).save(*args, **kwargs)


class FundCenter(models.Model):
    fundcenter = models.CharField(max_length=6, unique=True)
    shortname = models.CharField(max_length=25, null=True, blank=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default="",
        related_name="parent_fc",
    )

    def __str__(self):
        return f"{self.fundcenter} - {self.shortname}"

    def validate_unique(self, exclude=None):
        qs = FundCenter.objects.filter(fundcenter=self.fundcenter).exists()
        if qs:
            raise ValidationError("Fund center must be unique.")
        else:
            print("All good")

    def save(self, *args, **kwargs):
        self.validate_unique()
        self.fundcenter = self.fundcenter.upper()
        self.shortname = self.shortname.upper()
        super(FundCenter, self).save(*args, **kwargs)


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

    def __str__(self):
        return f"{self.costcenter} - {self.shortname}"

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
