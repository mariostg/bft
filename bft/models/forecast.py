
from django.conf import settings
from django.db import models

from bft import exceptions

class ForecastAdjustmentManager(models.Manager):
    """ForecastAdjustmentManager class manages forecast adjustments for fund centers and cost centers.

    This class extends Django's models.Manager to provide custom functionality for managing
    forecast adjustments. It allows querying and retrieving forecast adjustments for fund centers
    and their descendant cost centers.

    Methods:
        fundcenter_descendants(fundcenter: str, fund: str = None) -> dict:
            Retrieves forecast adjustments for all descendants of a specified fund center.

    Inherits From:
        models.Manager
    """

    def fundcenter_descendants(self, fundcenter: str, fund: str = None) -> dict:
        """
        Retrieves and formats forecast adjustments for cost centers within a fund center hierarchy.

        The function returns a list of dictionaries containing cost center information and their
        associated forecast adjustments, filtered by the specified fund center and optionally by fund.

        Args:
            fundcenter (str): The fund center code to retrieve descendants for.
            fund (str, optional): The fund code to filter results. Defaults to None.

        Returns:
            list: A list of dictionaries containing cost center and forecast adjustment information.
            Each dictionary includes:
                - Cost Element: The cost center code
                - Cost Element Name: The short name of the cost center
                - Fund Center ID: The cost center's ID
                - Fund: The associated fund code
                - Parent ID: The parent cost center's ID
                - Path: The cost center's sequence path
                - Parent Path: The parent cost center's sequence path
                - Parent Fund Center: The parent fund center code
                - Forecast Adjustment: The forecast adjustment amount (float)
                - Type: Always "CC" for Cost Center

        Example:
            >>> fundcenter_descendants('FC001', 'F001')
            [{'Cost Element': 'CC001', 'Cost Element Name': 'Operations', ...}]
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
    """A model representing adjustments made to financial forecasts.

    This model stores information about adjustments made to financial forecasts,
    including the cost center, fund, adjustment amount, and associated metadata.

    Attributes:
        costcenter (ForeignKey): Reference to the CostCenter model.
        fund (ForeignKey): Reference to the Fund model.
        amount (DecimalField): The adjustment amount with 2 decimal places.
        note (TextField): Optional notes about the adjustment.
        owner (ForeignKey): Reference to the user who created the adjustment.
        updated (DateTimeField): Timestamp of last update.
        created (DateTimeField): Timestamp of creation.

    Raises:
        LineItemsDoNotExistError: If the associated cost center has no line items.

    Example:
        >>> adjustment = ForecastAdjustment(
        ...     costcenter=cost_center,
        ...     fund=fund,
        ...     amount=1000.00,
        ...     note="Budget increase"
        ... )
        >>> adjustment.save()
    """
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
        """Save the forecast adjustment to the database.

        Validates that the associated cost center has line items before saving. If the cost center
        has no line items, raises a LineItemsDoNotExistError.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Raises:
            LineItemsDoNotExistError: If the associated cost center has no line items.

        """
        if not CostCenterManager().has_line_items(self.costcenter):
            raise exceptions.LineItemsDoNotExistError(
                f"{self.costcenter} has no line items.  Forecast adjustment rejected."
            )

        super().save(*args, **kwargs)

