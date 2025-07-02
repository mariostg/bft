
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.models import QuerySet

from bft import exceptions
from bft.conf import QUARTERKEYS, QUARTERS, YEAR_CHOICES


class AllocationQuerySet(models.QuerySet):
    """QuerySet for Allocation objects providing custom lookup methods.

    This QuerySet extends the base Django QuerySet to provide specialized filtering
    methods for Allocation objects based on various criteria like fund, cost center,
    fund center, etc.

    Methods:
        fund(fund: Fund | str) -> QuerySet | None:
            Filter allocations by fund. Accepts Fund object or fund code string.

        costcenter(costcenter: CostCenter | str) -> QuerySet | None:
            Filter allocations by cost center. Accepts CostCenter object or code string.

        descendants_fundcenter(fundcenter: FundCenter | str) -> QuerySet | None:
            Filter allocations by fund center and all its descendants based on sequence.
            Accepts FundCenter object or fund center code string.

        descendants_costcenter(fundcenter: FundCenter | str) -> QuerySet | None:
            Filter allocations by cost centers belonging to a fund center and its descendants.
            Accepts FundCenter object or fund center code string.

        fundcenter(fundcenter: FundCenter | str) -> QuerySet | None:
            Filter allocations by specific fund center.
            Accepts FundCenter object or fund center code string.

        fy(fy: int) -> QuerySet | None:
            Filter allocations by fiscal year.

        quarter(quarter: int) -> QuerySet | None:
            Filter allocations by quarter number.
            Quarter must be a valid quarter key.

    Returns:
        QuerySet: Filtered queryset based on the criteria
        None: If the lookup object doesn't exist or invalid input

    Note:
        All string inputs for fund, cost center, and fund center are converted to uppercase.
        Empty/None inputs return the original queryset without filtering.
    """

    def fund(self, fund: Fund | str) -> QuerySet | None:
        """Filter transactions by fund.

        Args:
            fund (Union[Fund, str]): Fund object or fund code string to filter by.
                If string is provided, it will be converted to uppercase and looked up.

        Returns:
            Union[QuerySet, None]: Filtered queryset if fund exists, None if fund string not found,
                or original queryset if no fund provided.
        """

        if not fund:
            return self
        if isinstance(fund, str):
            try:
                fund = Fund.objects.get(fund=fund.upper())
            except Fund.DoesNotExist:
                return None
        return self.filter(fund=fund)

    def costcenter(self, costcenter: CostCenter | str) -> QuerySet | None:
        """
        Filter queryset by cost center.

        This method filters the queryset based on a given cost center. It accepts either a
        CostCenter instance or a string representing the cost center code.

        Args:
            costcenter (Union[CostCenter, str]): The cost center to filter by. Can be either a
                CostCenter instance or a string representing the cost center code.

        Returns:
            Union[QuerySet, None]: Returns filtered queryset if cost center exists,
            original queryset if no cost center provided, or None if cost center not found.
        """

        if not costcenter:
            return self
        if isinstance(costcenter, str):
            try:
                costcenter = CostCenter.objects.get(costcenter=costcenter.upper())
            except CostCenter.DoesNotExist:
                return None
        return self.filter(costcenter=costcenter)

    def descendants_fundcenter(self, fundcenter: FundCenter | str) -> QuerySet | None:
        """
        Get all records associated with a given fund center and its descendants.

        This method filters the queryset to return only records that belong to the specified
        fund center and any of its descendant fund centers in the financial hierarchy.

        Args:
            fundcenter (Union[FundCenter, str]): The fund center object or fund center code string
                to filter by. If a string is provided, it will be converted to uppercase and
                looked up in the database.

        Returns:
            Union[QuerySet, None]: A QuerySet containing all records associated with the specified
                fund center and its descendants. Returns None if the provided fund center string
                does not exist in the database. Returns the original queryset if no fund center
                is provided.

        Example:
            >>> MyModel.objects.all().descendants_fundcenter('FC001')
            <QuerySet [<MyModel: record1>, <MyModel: record2>, ...]>
        """

        if not fundcenter:
            return self
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        fc_family = FundCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        return self.filter(fundcenter__in=fc_family)

    def descendants_costcenter(self, fundcenter: FundCenter | str) -> QuerySet | None:
        """
        Get queryset of Fund Center objects filtered by descendants of a given Fund Center.

        This method returns a queryset containing all Fund Center objects that are descendants
        of the specified Fund Center in the organizational hierarchy. The hierarchy is determined
        by the sequence attribute.

        Args:
            fundcenter (Union[FundCenter, str]): A FundCenter object or a string representing
                the fund center code to filter by.

        Returns:
            Union[QuerySet, None]: A queryset of Fund Center objects that are descendants of the
                specified fund center. Returns None if the provided fund center string doesn't
                exist, or returns self if fundcenter parameter is falsy.

        Example:
            >>> FundCenter.objects.descendants_costcenter('FC001')
            <QuerySet [<FundCenter: FC001-01>, <FundCenter: FC001-02>, ...]>
        """

        if not fundcenter:
            return self
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        cc_family = CostCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        return self.filter(costcenter__in=cc_family)

    def fundcenter(self, fundcenter: FundCenter | str) -> QuerySet | None:
        """
        Filter queryset by fund center.

        This method filters the queryset based on the provided fund center. If the fund center
        is provided as a string, it attempts to retrieve the corresponding FundCenter object
        from the database.

        Args:
            fundcenter (Union[FundCenter, str]): The fund center to filter by. Can be either
                a FundCenter instance or a string representing the fund center code.

        Returns:
            Union[QuerySet, None]: Returns the filtered queryset if the fund center exists,
                the original queryset if no fund center is provided, or None if the fund
                center cannot be found.
        """

        if not fundcenter:
            return self
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        return self.filter(fundcenter=fundcenter)

    def fy(self, fy: int) -> QuerySet | None:
        """Filter queryset by fiscal year.

        Args:
            fy (int): The fiscal year to filter by.

        Returns:
            QuerySet | None: Filtered queryset if fy is provided, otherwise returns the original queryset.
        """
        if not fy:
            return self
        return self.filter(fy=fy)

    def quarter(self, quarter: int) -> QuerySet | None:
        """
        Filter queryset by quarter.

        Args:
            quarter (int): Quarter number to filter by (1, 2, 3, or 4)

        Returns:
            QuerySet | None: Filtered queryset if valid quarter, None if invalid quarter,
                            or original queryset if no quarter specified

        Example:
            >>> MyModel.objects.quarter(2)  # Returns queryset filtered for Q2
            >>> MyModel.objects.quarter(5)  # Returns None (invalid quarter)
            >>> MyModel.objects.quarter(None)  # Returns original queryset
        """
        if not quarter:
            return self
        if str(quarter) not in QUARTERKEYS:
            return None
        return self.filter(quarter=quarter)


class Allocation(models.Model):
    """An abstract class that defines the common allocation related fields

    This model represents a financial allocation with common fields used across different allocation types.

    Attributes:
        fund (Fund): Foreign key to the associated Fund model.
        amount (Decimal): The allocation amount with 2 decimal places precision.
        fy (int): Fiscal year for the allocation.
        quarter (str): Quarter period of the allocation ('0', '1', '2', '3', '4').
        note (str, optional): Additional notes about the allocation.
        owner (User, optional): User who created/owns the allocation.
        updated (datetime): Timestamp of last update.
        created (datetime): Timestamp of creation.

    Methods:
        save(): Validates and saves the allocation.
            Raises:
                InvalidOptionException: If quarter value is invalid
                InvalidAllocationException: If amount is negative
                InvalidFiscalYearException: If fiscal year is invalid
                ValueError: If fund is not specified

    Meta:
    """

    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fy = models.PositiveSmallIntegerField(
        "Fiscal Year", choices=YEAR_CHOICES, default=datetime.now().year
    )
    quarter = models.CharField(max_length=1, choices=QUARTERS, default="0")
    note = models.TextField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.RESTRICT
    )
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True, null=True)

    objects = AllocationQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.fund} - {self.amount}"

    def save(self, *args, **kwargs):
        """
        Save allocation record after performing validation checks.

        Validates the following conditions before saving:
        - Quarter is valid according to QUARTERS choices
        - Amount is not negative
        - Fiscal year is valid according to YEAR_CHOICES
        - Fund is assigned

        Raises:
            InvalidOptionException: If quarter is not a valid choice
            InvalidAllocationException: If amount is negative
            InvalidFiscalYearException: If fiscal year is not valid
            ValueError: If fund is not assigned

        """

        if str(self.quarter) not in list(zip(*QUARTERS))[0]:
            raise exceptions.InvalidOptionException(
                f"Quarter {self.quarter} invalid.  Must be one of {','.join([x[0] for x in QUARTERS])}"
            )
        if self.amount < 0:
            raise exceptions.InvalidAllocationException(
                "Allocation less than 0 is invalid"
            )
        if self.fy not in [v[0] for v in YEAR_CHOICES]:
            raise exceptions.InvalidFiscalYearException(
                f"Fiscal year {self.fy} invalid, must be one of {','.join([v[1] for v in YEAR_CHOICES])}"
            )
        if not self.fund:
            raise ValueError("Allocation cannot be saved without Fund")
        super().save(*args, **kwargs)


class CostCenterAllocation(Allocation):
    """A class representing a cost center allocation in the budget forecasting system.

    This class extends the base Allocation model to include cost center specific allocations,
    ensuring that each combination of fund, cost center, quarter, and fiscal year is unique.

    Attributes:
        costcenter (ForeignKey): Reference to a CostCenter object, cannot be null

    Methods:
        __str__(): Returns a string representation of the allocation
        save(*args, **kwargs): Overrides the default save method to ensure costcenter is provided

    Raises:
        ValueError: If attempting to save without a cost center assigned

    Meta:
        verbose_name_plural: "Cost Center Allocations"
        constraints: Ensures unique combination of fund, costcenter, quarter, and fy
    """
    costcenter = models.ForeignKey(
        CostCenter, on_delete=models.CASCADE, null=True, verbose_name="Cost Center"
    )

    def __str__(self):
        return (
            f"{self.costcenter} - {self.fund} - {self.fy} Q{self.quarter} {self.amount}"
        )

    def save(self, *args, **kwargs):
        """
        Save a CostCenterAllocation instance to the database.

        Overrides the default save method to ensure a cost center is assigned before saving.

        Args:
            *args: Variable length argument list to pass to parent save method
            **kwargs: Arbitrary keyword arguments to pass to parent save method

        Raises:
            ValueError: If costcenter field is empty/None

        Returns:
            None
        """
        if not self.costcenter:
            raise ValueError(f"Allocation cannot be saved without Cost Center {self}")
        super(CostCenterAllocation, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Cost Center Allocations"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "costcenter",
                    "quarter",
                    "fy",
                ),
                name="unique_cost_center_allocation",
            )
        ]


class FundCenterAllocation(Allocation):
    """A model representing fund allocations to Fund Centers.

    This class extends the base Allocation model to track financial allocations
    specifically assigned to Fund Centers. Each allocation is uniquely identified
    by the combination of fund, fund center, fiscal quarter, and fiscal year.

    Attributes:
        fundcenter (FundCenter): Foreign key to the FundCenter model representing
            the fund center receiving the allocation.

    Example:
        >>> allocation = FundCenterAllocation(
        ...     fundcenter=some_fundcenter,
        ...     fund=some_fund,
        ...     fy=2023,
        ...     quarter=1,
        ...     amount=1000.00
        ... )
    """
    fundcenter = models.ForeignKey(
        FundCenter, on_delete=models.CASCADE, null=True, verbose_name="Fund Center"
    )

    def __str__(self):
        return (
            f"{self.fundcenter} - {self.fund} - {self.fy}Q{self.quarter} {self.amount}"
        )

    class Meta:
        verbose_name_plural = "Fund Center Allocations"
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "fundcenter",
                    "quarter",
                    "fy",
                ),
                name="unique_fund_center_allocation",
            )
        ]
