from django.db import models


class CostCenterMonthly(models.Model):
    fund = models.CharField("Fund", max_length=4)
    source = models.CharField("Source", max_length=24)
    costcenter = models.CharField("Cost Center", max_length=6)

    period = models.CharField("Period", max_length=2)
    fy = models.CharField("FY", max_length=4)

    spent = models.DecimalField("Spent", max_digits=10, decimal_places=2, default=0, null=True)
    commitment = models.DecimalField("Commitment", max_digits=10, decimal_places=2, default=0, null=True)
    pre_commitment = models.DecimalField("Pre Commitment", max_digits=10, decimal_places=2, default=0, null=True)
    fund_reservation = models.DecimalField("Fund Reservation", max_digits=10, decimal_places=2, default=0, null=True)
    balance = models.DecimalField("Balance", max_digits=10, decimal_places=2, default=0, null=True)
    working_plan = models.DecimalField("Working Plan", max_digits=10, decimal_places=2, default=0, null=True)

    def __str__(self):
        s = ""
        field_names = [field.name for field in self._meta.fields]
        for fn in field_names:
            s += f"{fn} : {getattr(self,fn)}\n"
        return s

    class Meta:
        verbose_name_plural = "Cost Center Monthly"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "source",
                    "costcenter",
                    "period",
                    "fy",
                ),
                name="unique_cost_center_monthly_row",
            )
        ]
