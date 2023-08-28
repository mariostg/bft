from django.db import models


class CostCenterMonthly(models.Model):
    fund = models.CharField(max_length=4)
    source = models.CharField(max_length=24)
    cost_center = models.CharField("Cost Center", max_length=6)

    period = models.CharField(max_length=2)
    fy = models.CharField(max_length=4)

    spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commitment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pre_commitment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fund_reservation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    working_plan = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    allocation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    forecast = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    forecast_ajustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        s = ""
        field_names = [field.name for field in self._meta.fields]
        for fn in field_names:
            s += f"{fn} : {getattr(self,fn)}\n"
        return s

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "source",
                    "cost_center",
                    "period",
                    "fy",
                ),
                name="unique_cost_center_monthly_row",
            )
        ]
