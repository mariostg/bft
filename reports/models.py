from django.db import models


class MonthlyDataQuerySet(models.QuerySet):
    def fund(self, fund: str = None):
        if not fund:
            return self
        return self.filter(fund=fund)

    def fy(self, fy: int = None):
        if not fy:
            return self
        return self.filter(fy=fy)

    def period(self, period: int = None):
        if not period:
            return self
        return self.filter(period=period)

    def costcenter(self, costcenter: str = None):
        if not costcenter:
            return self
        return self.filter(costcenter=costcenter)


class MonthlyData(models.Model):
    """A generic base class that contains generic fields to be used by other classes that needs monthly related fields."""
    fund = models.CharField("Fund", max_length=4)
    source = models.CharField("Source", max_length=24)
    costcenter = models.CharField("Cost Center", max_length=6)

    period = models.CharField("Period", max_length=2)
    fy = models.CharField("FY", max_length=4)

    objects = models.Manager()
    search = MonthlyDataQuerySet.as_manager()

    def __str__(self):
        s = ""
        field_names = [field.name for field in self._meta.fields]
        for fn in field_names:
            s += f"{fn} : {getattr(self,fn)}\n"
        return s

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "source",
                    "costcenter",
                    "period",
                    "fy",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]


class CostCenterMonthlyAllocation(MonthlyData):
    """A class to handle the monthly values of allocation"""

    allocation = models.DecimalField("Allocation", max_digits=10, decimal_places=2, default=0, null=True)

    class Meta(MonthlyData.Meta):
        verbose_name_plural = "Cost Center Monthly Allocations"


class CostCenterMonthlyForecastAdjustment(MonthlyData):
    """A class to handle the monthly values of forecast adjustment"""

    forecast_adjustment = models.DecimalField(
        "Forecast Adjustment", max_digits=10, decimal_places=2, default=0, null=True
    )

    class Meta(MonthlyData.Meta):
        verbose_name_plural = "Cost Center Monthly Forecast Adjustment"


class CostCenterMonthlyLineItemForecast(MonthlyData):
    """A class to handle the monthly values of of Line Items forecast"""

    line_item_forecast = models.DecimalField(
        "Line Item Forecast", max_digits=10, decimal_places=2, default=0, null=True
    )

    class Meta(MonthlyData.Meta):
        verbose_name_plural = "Line Item Monthly Forecast"


class CostCenterMonthlyEncumbrance(MonthlyData):

    spent = models.DecimalField("Spent", max_digits=10, decimal_places=2, default=0, null=True)
    commitment = models.DecimalField("Commitment", max_digits=10, decimal_places=2, default=0, null=True)
    pre_commitment = models.DecimalField("Pre Commitment", max_digits=10, decimal_places=2, default=0, null=True)
    fund_reservation = models.DecimalField("Fund Reservation", max_digits=10, decimal_places=2, default=0, null=True)
    balance = models.DecimalField("Balance", max_digits=10, decimal_places=2, default=0, null=True)
    working_plan = models.DecimalField("Working Plan", max_digits=10, decimal_places=2, default=0, null=True)

    class Meta(MonthlyData.Meta):
        verbose_name_plural = "Cost Center Monthly Encumbrance"


class CostCenterInYearEncumbrance(MonthlyData):

    spent = models.DecimalField("Spent", max_digits=10, decimal_places=2, default=0, null=True)
    commitment = models.DecimalField("Commitment", max_digits=10, decimal_places=2, default=0, null=True)
    pre_commitment = models.DecimalField("Pre Commitment", max_digits=10, decimal_places=2, default=0, null=True)
    fund_reservation = models.DecimalField("Fund Reservation", max_digits=10, decimal_places=2, default=0, null=True)
    balance = models.DecimalField("Balance", max_digits=10, decimal_places=2, default=0, null=True)
    working_plan = models.DecimalField("Working Plan", max_digits=10, decimal_places=2, default=0, null=True)

    class Meta(MonthlyData.Meta):
        verbose_name_plural = "Cost Center In Year Encumbrance"
