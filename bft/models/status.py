
from django.db import models

from bft import conf
from bft.conf import PERIODS, QUARTERS, STATUS

class BftStatusManager(models.Manager):
    """BftStatusManager is a custom model manager for handling BftStatus objects.

    This manager provides methods to retrieve specific status values from the BftStatus model,
    focusing on fiscal year (FY), quarter, and period information.

    Methods:
        fy() -> str | None:
            Retrieves the value associated with the "FY" status.
            Returns None if the status does not exist.

        quarter() -> str | None:
            Retrieves the value associated with the "QUARTER" status.
            Returns None if the status does not exist.

        period() -> str | None:
            Retrieves the value associated with the "PERIOD" status.
            Returns None if the status does not exist.
    """

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
    """A model representing the status of BFT (Business Forecasting Tool).

    This model stores and manages different statuses and their corresponding values,
    with built-in validation for quarters and periods.

    Attributes:
        status (CharField): The status identifier, must be one of predefined STATUS choices.
        value (CharField): The value associated with the status.
        objects (Manager): Default model manager.
        current (BftStatusManager): Custom manager for status-specific operations.

    Methods:
        __str__(): Returns a string representation in format "status:value".
        save(*args, **kwargs): Custom save method with validation logic for status and values.

    Raises:
        AttributeError: If the status is not one of the predefined STATUS choices.
        ValueError: If the value is invalid for QUARTER or PERIOD status types.

    Example:
        status = BftStatus(status='QUARTER', value='Q1')
        status.save()  # Will validate before saving
    """

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
