from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.db import models

from bft import exceptions
from bft.conf import QUARTERS, YEAR_CHOICES

class CapitalProjectManager(models.Manager):
    """Manager class for CapitalProject model.

    This class provides utility methods for managing CapitalProject objects,
    including fetching projects, checking existence, and handling request parameters.

    Methods:
        project(capital_project: str) -> "CapitalProject | None":
            Retrieves a capital project by its project number.
            Returns None if project doesn't exist.

        exists(capital_project: str = None) -> bool:
            Checks if a specific capital project exists or if any projects exist.
            If capital_project is provided, checks for that specific project.
            If no argument provided, checks if any projects exist at all.

        get_request(request) -> str | None:
            Extracts and validates capital project number from request parameters.
            Adds info message if project doesn't exist.
            Returns uppercase project number or None if not provided.
    """
    def project(self, capital_project: str) -> "CapitalProject | None":
        """
        Retrieve a CapitalProject object by its project number.

        Args:
            capital_project (str): The project number to search for.

        Returns:
            CapitalProject | None: The matching CapitalProject object if found, None otherwise.

        The search is case-insensitive - the input string is converted to uppercase
        before querying the database.
        """
        capital_project = capital_project.upper()
        try:
            obj = CapitalProject.objects.get(project_no__iexact=capital_project)
        except CapitalProject.DoesNotExist:
            return None
        return obj

    def exists(self, capital_project: str = None) -> bool:
        """Check if a specific capital project exists or if any capital projects exist.

        Args:
            capital_project (str, optional): The project number to check for.
                If None, checks if any capital projects exist in the database.
                Defaults to None.

        Returns:
            bool: True if the specified project exists (or any projects exist if no specific
                project was provided), False otherwise.

        Note:
            When checking for a specific project, the project number comparison is case-insensitive
            as the input is converted to uppercase.
        """
        if capital_project:
            return CapitalProject.objects.filter(
                project_no=capital_project.upper()
            ).exists()
        else:
            return CapitalProject.objects.count() > 0

    def get_request(self, request) -> str | None:
        """
        Retrieves and validates the capital project parameter from an HTTP request.

        Args:
            request: The HTTP request object containing potential capital_project parameter.

        Returns:
            str | None: The uppercase capital project string if found and valid, None otherwise.
                If project exists but is invalid, adds info message to request and returns project.
        """
        capital_project = request.GET.get("capital_project")
        if capital_project:
            capital_project = capital_project.upper()
            if not CapitalProjectManager().exists(capital_project):
                messages.info(
                    request, f"Capital Project {capital_project} does not exist."
                )
            return capital_project
        else:
            return None


class CapitalProject(models.Model):
    """A Django model representing a Capital Project within the financial system.

    This model stores information about capital projects including their project numbers,
    names, fund center associations, and procurement officers.

    Attributes:
        project_no (CharField): Unique 8-character project number identifier
        shortname (CharField): 35-character project name/description (optional)
        isupdatable (BooleanField): Flag indicating if project can be updated during the DRMIS download
        note (TextField): Additional notes about the project (optional)
        fundcenter (ForeignKey): Associated Fund Center for the project
        procurement_officer (ForeignKey): Assigned procurement officer user (optional)
        objects (CapitalProjectManager): Custom model manager for Capital Projects

    Methods:
        __str__(): Returns string representation as "PROJECT_NO - SHORTNAME"
        save(): Overrides default save to enforce uppercase for project_no and shortname

    Meta:
        ordering: Orders projects by project_no
        verbose_name_plural: Sets plural name to "Capital Projects"
    """
    project_no = models.CharField("Project No", max_length=8, unique=True)
    shortname = models.CharField("Project Name", max_length=35, blank=True)
    isupdatable = models.BooleanField("Is Updatable", default=False)
    note = models.TextField(null=True, blank=True)
    # sequence = models.CharField("CC Path", max_length=25, unique=True, default="")
    fundcenter = models.ForeignKey(
        FundCenter,
        on_delete=models.RESTRICT,
        default="0",
        related_name="capital_projects",
        verbose_name="Fund Center",
    )
    procurement_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        limit_choices_to={"procurement_officer": True},
    )
    objects = CapitalProjectManager()

    def __str__(self):
        return f"{self.project_no.upper()} - {self.shortname}"

    class Meta:
        ordering = ["project_no"]
        verbose_name_plural = "Capital Projects"

    def save(self, *args, **kwargs):
        """
        Save method override for CapitalProject model.

        This method performs the following operations before saving:
        1. Converts project_no to uppercase
        2. If shortname exists, converts it to uppercase

        Args:
            *args: Variable length argument list for save method
            **kwargs: Arbitrary keyword arguments for save method

        Returns:
            None

        Note:
            This method calls the parent class's save method after performing
            the uppercase conversions.
        """

        self.project_no = self.project_no.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        super(CapitalProject, self).save(*args, **kwargs)


class CapitalForecasting(models.Model):
    """A base abstract model for capital forecasting data.

    This class serves as an abstract base model for tracking and managing capital forecasting
    across different funds, fiscal years, and capital projects.

    Attributes:
        fund (Fund): Foreign key to the Fund model.
        fy (int): Fiscal year for the forecast, defaulting to current year.
        capital_project (CapitalProject): Foreign key to the associated capital project.
        commit_item (int): Commitment item number, defaults to 0.
        notes (str): Optional text field for additional notes.

    Constraints:
        - Unique constraint on combination of fund, capital_project, commit_item, and fy.
        - Fiscal year must be one of the predefined YEAR_CHOICES.
        - Fund cannot be null when saving.

    Raises:
        InvalidFiscalYearException: If the fiscal year is not in YEAR_CHOICES.
        ValueError: If attempting to save without a fund assigned.
    """

    fund = models.ForeignKey(Fund, on_delete=models.CASCADE, null=True)
    fy = models.PositiveSmallIntegerField(
        "Fiscal Year", choices=YEAR_CHOICES, default=datetime.now().year
    )
    capital_project = models.ForeignKey(
        CapitalProject,
        on_delete=models.CASCADE,
        null=True,
        verbose_name="Capital Project",
    )
    commit_item = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "capital_project",
                    "commit_item",
                    "fy",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]

    def __str__(self):
        return f"{self.capital_project} - {self.fy} - {self.fund.fund}"

    def save(self, *args, **kwargs):
        """
        Saves the instance to the database after validating fiscal year and fund.

        Raises:
            InvalidFiscalYearException: If the fiscal year is not one of the valid choices defined in YEAR_CHOICES.
            ValueError: If the fund field is empty or None.

        Args:
            *args: Variable length argument list to pass to parent save method
            **kwargs: Arbitrary keyword arguments to pass to parent save method
        """
        if self.fy not in [v[0] for v in YEAR_CHOICES]:
            raise exceptions.InvalidFiscalYearException(
                f"Fiscal year {self.fy} invalid, must be one of {','.join([v[1] for v in YEAR_CHOICES])}"
            )
        if not self.fund:
            raise ValueError("Allocation cannot be saved without Fund")
        super().save(*args, **kwargs)


class CapitalYearEnd(CapitalForecasting):
    """Class representing capital spending at the end of the year.

    A subclass of CapitalForecasting that tracks the actual amount spent
    on capital expenses at year end.

    Attributes:
        ye_spent (PositiveIntegerField): The total amount of capital spent at year end.
                                        Defaults to 0.
    """
    ye_spent = models.PositiveIntegerField(default=0)


class CapitalNewYear(CapitalForecasting):
    """A model representing financial capital starting point at beginning of new year.

    Inherits from CapitalForecasting model and adds initial allocation tracking.

    Attributes:
        initial_allocation (PositiveIntegerField): The starting capital amount allocated
            for the new year period. Defaults to 0.
    """
    initial_allocation = models.PositiveIntegerField("Initial allocation", default=0)


class CapitalInYear(CapitalForecasting):
    """A class representing capital allocations and expenditures within a specific fiscal year and quarter.

    This model extends CapitalForecasting to track detailed capital planning information
    including quarterly allocations, spending, and various commitment categories.

    Attributes:
        quarter (str): The quarter designation (0-4), with 0 being the default
        allocation (int): The allocated budget amount for the period
        spent (int): The amount spent from the allocation
        co (int): Construction amount
        pc (int): Pre-construction amount
        fr (int): Furniture amount
        le (int): Labor external amount
        mle (int): Misc labor external amount
        he (int): Hourly employee amount

    Note:
        The combination of fund, capital_project, commit_item, fiscal year and quarter
        must be unique per database constraint.
    """
    quarter = models.CharField(max_length=1, choices=QUARTERS, default="0")
    allocation = models.PositiveIntegerField(default=0)
    spent = models.PositiveIntegerField(default=0)
    co = models.PositiveIntegerField(default=0)
    pc = models.PositiveIntegerField(default=0)
    fr = models.PositiveIntegerField(default=0)
    le = models.PositiveIntegerField(default=0)
    mle = models.PositiveIntegerField(default=0)
    he = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fund",
                    "capital_project",
                    "commit_item",
                    "fy",
                    "quarter",
                ),
                name="capital_in_year_is_unique",
            )
        ]
