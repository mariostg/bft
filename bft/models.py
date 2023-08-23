from datetime import datetime
from django.db import models
from bft.conf import YEAR_CHOICES, QUARTERS, PERIODS, STATUS

# Create your models here.
class BftStatus(models.Model):
    status = models.CharField("Status", max_length=30, unique=True, choices=STATUS)
    value = models.CharField("Value", max_length=30)

    def __str__(self) -> str:
        return f"{self.status}:{self.value}"

    def save(self, *args, **kwargs):
        status, _ = zip(*STATUS)
        if self.status not in status:
            raise AttributeError(f"{self.status} not a valid status")
        super(BftStatus, self).save(*args, **kwargs)
