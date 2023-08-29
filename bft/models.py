from datetime import datetime
from django.db import models
from django.db.models import Q
from bft.conf import YEAR_CHOICES, QUARTERS, PERIODS, STATUS
from bft import conf

# Create your models here.
class BftStatusManager(models.Manager):
    def fy(self) -> str:
        return BftStatus.objects.get(status="FY").value

    def quarter(self) -> str:
        return BftStatus.objects.get(status="QUARTER").value

    def period(self) -> str:
        return BftStatus.objects.get(status="PERIOD").value


class BftStatus(models.Model):
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

    current = BftStatusManager
