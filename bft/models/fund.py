
import pandas as pd
from django.contrib import messages
from django.db import IntegrityError, models
from django.db.models import QuerySet
from django.forms.models import model_to_dict

from utils.dataframe import BFTDataFrame

class FundManager(models.Manager):
    """Fund object manager class.

    This class manages Fund objects in the database, providing methods to retrieve,
    check existence, and handle web requests related to funds.

    Methods:
        fund(fund: str) -> Fund | None:
            Retrieves a Fund object given its fund string identifier.

        pk(pk: int) -> Fund | None:
            Retrieves a Fund object given its primary key.

        exists(fund: str) -> bool:
            Checks if a fund exists in the database.

        get_request(request) -> str | None:
            Processes an HTTP request to extract and validate a fund identifier.
    """
    def fund(self, fund: str):
        """
        Retrieves a Fund object from the database based on the provided fund name.

        Args:
            fund (str): The name of the fund to search for (case-insensitive)

        Returns:
            Fund: The matching Fund object if found
            None: If no matching Fund is found in the database

        Examples:
            >>> fund_obj = model.fund("C113")
            >>> if fund_obj:
            ...     print(fund_obj.name)
            ... else:
            ...     print("Fund not found")
        """

        try:
            obj = Fund.objects.get(fund__iexact=fund)
        except Fund.DoesNotExist:
            return None
        return obj

    def pk(self, pk: int):
        """Get a fund object given the primary key

        Args:
            pk (int): Primary key identifier of the fund

        Returns:
            Fund | None: Fund object if found, None if fund does not exist

        Examples:
            >>> fund = Fund.pk(1)  # Returns Fund object with pk=1
            >>> fund = Fund.pk(999)  # Returns None if fund not found
        """

        try:
            obj = Fund.objects.get(pk=pk)
        except Fund.DoesNotExist:
            return None
        return obj

    def exists(self, fund: str) -> bool:
        """Check if a fund exists in the database.

        Args:
            fund (str): The fund identifier to check for existence.

        Returns:
            bool: True if the fund exists in the database, False otherwise.
        """
        return Fund.objects.filter(fund=fund).exists()

    def get_request(self, request) -> str | None:
        """
        Extracts and validates a fund parameter from an HTTP request.

        Args:
            request: The HTTP request object containing GET parameters.

        Returns:
            str | None: The uppercase fund identifier if valid, empty string if fund doesn't exist,
            or None if no fund parameter was provided.

        Notes:
            - The fund parameter is case-insensitive as it's converted to uppercase.
            - Displays an info message to the user if the requested fund doesn't exist.
        """
        fund = request.GET.get("fund")
        if fund:
            fund = fund.upper()
            if not FundManager().exists(fund):
                messages.info(request, f"Fund {fund} does not exist.")
                return ""
            return fund
        else:
            return None


class Fund(models.Model):
    """A Django model representing a financial fund as defined in DRMIS.

    This class represents a fund with basic information including its code, name,
    vote status, and download flag. The fund code must be a 4-character string
    starting with a letter, the vote must be either '0', '1' or '5'.

    Attributes:
        fund (str): A unique 4-character fund identifier code.
        name (str): The fund's display name (up to 30 characters).
        vote (str): A single character vote status ('0', '1', or '5').
        download (bool): Flag indicating if the fund should be downloaded.

    Methods:
        clean_vote(): Validates the vote field.
        clean_fund(): Validates the fund code format.
        save(*args, **kwargs): Overrides the default save method to perform validation.

    Meta:
        ordering: Orders by download status (descending) then fund code.
        verbose_name_plural: Sets plural name to "Funds".

    Raises:
        ValueError: If fund code or vote validation fails.
    """
    fund = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=30)
    vote = models.CharField(max_length=1)
    download = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fund} - {self.name}"

    class Meta:
        ordering = ["-download", "fund"]
        verbose_name_plural = "Funds"

    def clean_vote(self):
        """
        Clean and validate the vote value.

        The vote can only be "1", "5", or "0". The method converts the vote to string
        and validates if it matches the accepted values.

        Raises:
            ValueError: If the vote is not "1", "5", or "0", with a message indicating
                       the invalid value provided.
        """
        self.vote = str(self.vote)
        if self.vote != "1" and self.vote != "5" and self.vote != "0":
            raise ValueError(f"Vote must be 1 or 5, you provided [{self.vote}]")

    def clean_fund(self):
        """
        Validates and cleans the fund code.

        The fund code must follow these rules:
        - Must be exactly 4 characters long
        - Must begin with a letter
        - Can be "----" (special case that bypasses validation)

        Raises:
            ValueError: If the fund code doesn't begin with a letter
            ValueError: If the fund code is not exactly 4 characters long

        Returns:
            None: If fund is "----"
            implicitly returns None if validation passes
        """
        if self.fund == "----":
            return
        if not self.fund[0].isalpha():
            raise ValueError("Fund must begin with a letter")
        if len(self.fund) != 4:
            raise ValueError("Fund must be 4 characters long.")

    def save(self, *args, **kwargs):
        """
        Save method for Fund model.

        Performs the following operations before saving:
        1. Converts fund name to uppercase
        2. Cleans fund data
        3. Cleans vote data

        Args:
            *args: Variable length argument list to pass to parent save method
            **kwargs: Arbitrary keyword arguments to pass to parent save method

        Extends:
            django.db.models.Model.save()
        """
        self.fund = self.fund.upper()
        self.clean_fund()
        self.clean_vote()
        super(Fund, self).save(*args, **kwargs)

    objects = FundManager()


class FundCenterManager(models.Manager):
    """Manages Fund Center related database operations and data transformations.

    This manager class provides methods to handle Fund Center operations, including:
    - Fund center lookup and validation
    - Hierarchical relationship management (parents, descendants)
    - Data transformation to pandas DataFrames
    - Allocation management and reporting

    Methods:
        fundcenter(fundcenter: str) -> FundCenter | None:
            Retrieves a FundCenter object by its code (case-insensitive).

        pk(pk: int) -> FundCenter | None:
            Retrieves a FundCenter object by its primary key.

        get_sub_alloc(parent_alloc: FundCenterAllocation) -> FundCenterAllocation:
            Gets sub-allocations for a given parent allocation.

        sequence_exist(sequence) -> bool:
            Checks if a sequence exists in the database.

        fund_center_dataframe(data: QuerySet) -> pd.DataFrame:
            Converts fund center data to a pandas DataFrame.

        allocation_dataframe(fundcenter, fund, fy, quarter) -> pd.DataFrame:
            Creates a DataFrame of allocations based on provided filters.

        get_direct_descendants(fundcenter: FundCenter|str) -> list | None:
            Returns immediate child fund centers and cost centers.

        get_direct_descendants_dataframe(fundcenter: FundCenter|str) -> pd.DataFrame:
            Returns descendants as a DataFrame.

        get_fund_centers(parent: FundCenter|str) -> list:
            Returns child fund centers for a given parent.

        get_cost_centers(parent: FundCenter|str) -> list:
            Returns child cost centers for a given parent.

        exists(fundcenter: str = None) -> bool:
            Checks if a specific fund center exists.

        get_request(request) -> str | None:
            Extracts and validates fund center from HTTP request.
    """
    def fundcenter(self, fundcenter: str) -> "FundCenter | None":
        """
        Retrieve a FundCenter object based on the provided fund center code.

        Args:
            fundcenter (str): The fund center code to search for.

        Returns:
            FundCenter | None: The matching FundCenter object if found, None otherwise.

        Note:
            The search is case-insensitive, but the input is converted to uppercase before querying.
        """

        fundcenter = fundcenter.upper()
        try:
            obj = FundCenter.objects.filter(fundcenter__iexact=fundcenter)[0]
        except FundCenter.DoesNotExist:
            return None
        except IndexError:
            return None
        return obj

    def pk(self, pk: int):
        """
        Retrieves a FundCenter object by its primary key.

        Args:
            pk (int): The primary key of the FundCenter object to retrieve.

        Returns:
            FundCenter|None: The FundCenter object if found, None otherwise.
        """

        try:
            obj = FundCenter.objects.get(pk=pk)
        except FundCenter.DoesNotExist:
            return None
        return obj

    def get_sub_alloc(
        self, parent_alloc: "FundCenterAllocation"
    ) -> "FundCenterAllocation":
        """
        Retrieves sub-allocations for a given parent fund center allocation.

        This method finds all direct descendant fund centers of the parent allocation's fund center,
        and returns their corresponding allocations that match the parent's fiscal year,
        fund and quarter.

        Args:
            parent_alloc (FundCenterAllocation): The parent fund center allocation object

        Returns:
            QuerySet[FundCenterAllocation]: A queryset of FundCenterAllocation objects representing
                the sub-allocations of the parent fund center for the same fiscal year,
                fund and quarter.
        """
        seq = [
            s["sequence"] for s in self.get_direct_descendants(parent_alloc.fundcenter)
        ]
        dd = FundCenter.objects.filter(sequence__in=seq)
        return FundCenterAllocation.objects.filter(
            fundcenter__in=dd,
            fy=parent_alloc.fy,
            fund=parent_alloc.fund,
            quarter=parent_alloc.quarter,
        )

    def sequence_exist(self, sequence):
        """
        Check if a sequence already exists in the FundCenter model.

        Args:
            sequence: A sequence value to check for existence.

        Returns:
            bool: True if the sequence exists, False otherwise.
        """
        return FundCenter.objects.filter(sequence=sequence).exists()

    def fund_center_dataframe(self, data: QuerySet) -> pd.DataFrame:
        """
        Converts a QuerySet of fund centers into a pandas DataFrame.

        This method processes fund center data and ensures proper formatting of the parent IDs.
        Empty QuerySets will return an empty DataFrame.

        Args:
            data (QuerySet): A Django QuerySet containing fund center records

        Returns:
            pd.DataFrame: A pandas DataFrame with fund center data. The Fundcenter_parent_ID
            column is converted to integer type with null values replaced by 0.
        """

        if not data.count():
            return pd.DataFrame()
        df = BFTDataFrame(FundCenter).build(data)

        df["Fundcenter_parent_ID"] = df["Fundcenter_parent_ID"].fillna(0).astype("int")
        return df

    def allocation_dataframe(
        self,
        fundcenter: "FundCenter|str" = None,
        fund: "Fund|str" = None,
        fy: int = None,
        quarter: str = None,
    ) -> pd.DataFrame:
        """
        Retrieves fund center allocation data and returns it as a pandas DataFrame.

        This method queries FundCenterAllocation objects based on the provided filters and
        formats the data into a DataFrame with renamed columns for better readability.

        Parameters
        ----------
        fundcenter : FundCenter or str, optional
            Fund center object or fund center code to filter allocations
        fund : Fund or str, optional
            Fund object or fund code to filter allocations
        fy : int, optional
            Fiscal year to filter allocations
        quarter : str, optional
            Quarter to filter allocations

        Returns
        -------
        pandas.DataFrame
            DataFrame containing the allocation data with the following columns:
            - Allocation: Amount allocated
            - FY: Fiscal year
            - Quarter: Quarter
            - Fund Center: Fund center code
            - Fund: Fund code

        Examples
        --------
        >>> model.allocation_dataframe(fundcenter='2184BA', fy=2023, quarter='Q1')
           Allocation   FY Quarter Fund Center  Fund
        0     100000  2023      Q1      2184BA  F123
        """
        data = (
            FundCenterAllocation.objects.fundcenter(fundcenter)
            .fund(fund)
            .fy(fy)
            .quarter(quarter)
        )
        rename_columns = {
            "amount": "Allocation",
            "fy": "FY",
            "quarter": "Quarter",
            "fundcenter__fundcenter": "Fund Center",
            "fund__fund": "Fund",
        }
        try:
            df = pd.DataFrame(data).rename(columns=rename_columns)
        except ValueError:
            if not isinstance(data, dict):
                data = model_to_dict(data)
            df = pd.DataFrame([data]).rename(columns=rename_columns)

        return df

    def get_direct_descendants(self, fundcenter: "FundCenter|str") -> list | None:
        """
        Get direct descendant fund centers and cost centers of a given fund center.

        Args:
            fundcenter (Union[FundCenter, str]): Fund center object or fund center code string.

        Returns:
            Union[list, None]: List containing direct descendant fund centers and cost centers.
                Returns empty list if fundcenter argument is empty.
                Returns None if provided fund center string does not exist.
        """
        if not fundcenter:
            return []
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        return self.get_fund_centers(fundcenter) + self.get_cost_centers(fundcenter)

    def get_direct_descendants_dataframe(
        self, fundcenter: "FundCenter|str"
    ) -> list | None:
        """
        Get direct descendants of a fund center as a pandas DataFrame.

        This method retrieves all direct child fund centers and cost centers for a given fund center
        and combines them into a single DataFrame.

        Args:
            fundcenter (Union[FundCenter, str]): The fund center object or fund center code string

        Returns:
            Union[pandas.DataFrame, None]: DataFrame containing combined fund centers and cost centers data.
            Returns None if the fund center string provided doesn't exist.

        Example:
            >>> fc = FundCenter.objects.get(fundcenter='FC001')
            >>> descendants_df = fc.get_direct_descendants_dataframe(fc)
        """

        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter.upper())
            except FundCenter.DoesNotExist:
                return None
        fc = pd.DataFrame(self.get_fund_centers(fundcenter))
        cc = pd.DataFrame(self.get_cost_centers(fundcenter))
        return pd.concat([fc, cc])

    def get_fund_centers(self, parent: "FundCenter|str") -> list:
        """Get all fund centers under a given parent.

        Args:
            parent (Union[FundCenter, str]): Parent fund center object or fund center string equivalent

        Returns:
            list: List of fund center dictionaries containing all children fund centers under the given parent

        Example:
            >>> center = FundCenter.objects.get(id='FC001')
            >>> get_fund_centers(center)
            [{'id': 'FC002', 'name': 'Child Center 1'}, {'id': 'FC003', 'name': 'Child Center 2'}]
        """
        if isinstance(parent, str):
            parent = self.fundcenter(parent)
        return list(FundCenter.objects.filter(fundcenter_parent=parent).values())

    def get_cost_centers(self, parent: "FundCenter|str") -> list:
        """
        Retrieves all cost centers associated with a specific parent fund center.

        Args:
            parent (Union[FundCenter, str]): The parent fund center object or its string equivalent.

        Returns:
            list: A list of dictionaries containing the cost center data. Each dictionary
                  contains the field values for a cost center associated with the parent.

        Example:
            >>> fund.get_cost_centers('FC123')
            [{'id': 'CC100', 'name': 'Cost Center 1', ...}, {'id': 'CC101', 'name': 'Cost Center 2', ...}]
        """
        if isinstance(parent, str):
            parent = self.fundcenter(parent)
        return list(CostCenter.objects.filter(costcenter_parent=parent).values())

    def exists(self, fundcenter: str = None) -> bool:
        """Check if one or all FundCenter(s) exists.

        This method checks whether a specific fund center exists when a fundcenter parameter is provided,
        or if any fund centers exist in the database when no parameter is provided.

        Args:
            fundcenter (str, optional): The fund center code to check for existence.
                                       Defaults to None.

        Returns:
            bool: True if the specified fund center exists (when fundcenter is provided)
                  or if any fund centers exist (when fundcenter is None),
                  False otherwise.
        """
        if fundcenter:
            return FundCenter.objects.filter(fundcenter=fundcenter.upper()).exists()
        else:
            return FundCenter.objects.count() > 0

    def get_request(self, request) -> str | None:
        """Get fund center string from request if it exists.

        This method extracts the fund center from the GET parameters of the request,
        converts it to uppercase, validates its existence and returns it.
        If no fund center is provided, returns None.

        Args:
            request: The HTTP request object containing GET parameters.

        Returns:
            str | None: The uppercase fund center string if it exists in request,
                        None otherwise.
        """
        fundcenter = request.GET.get("fundcenter")
        if fundcenter:
            fundcenter = fundcenter.upper()
            if not FundCenterManager().exists(fundcenter):
                messages.info(request, f"Fund Center {fundcenter} does not exist.")
            return fundcenter
        else:
            return None


class FundCenter(models.Model):
    """A Fund Center model representing financial organizational units.

    This model represents financial fund centers in a hierarchical structure, where each fund
    center can have a parent fund center and multiple child fund centers.

    Attributes:
        fundcenter (str): A 6-character code identifying the fund center.
        shortname (str): An optional 25-character name/description of the fund center.
        sequence (str): A dot-separated path string representing the hierarchical structure.
        level (int): The depth level in the hierarchy tree (default=0).
        fundcenter_parent (ForeignKey): Reference to parent fund center, if any.

    Methods:
        __str__(): Returns a string representation in format "FUNDCENTER - SHORTNAME".
        save(): Custom save method that:
            - Handles sequence generation for root nodes
            - Prevents self-referential parent assignments
            - Updates sequence based on parent relationship
            - Normalizes fundcenter and shortname to uppercase
            - Calculates hierarchy level

    Meta:
        ordering: Orders by fundcenter field
        constraints: Ensures unique combination of fundcenter and parent
    """
    fundcenter = models.CharField("Fund Center", max_length=6)
    shortname = models.CharField(
        "Fund Center Name", max_length=25, null=True, blank=True
    )
    sequence = models.CharField("FC Path", max_length=25)
    level = models.SmallIntegerField("Level", default=0)
    fundcenter_parent = models.ForeignKey(
        "self",
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        default=None,
        related_name="parent_fc",
        verbose_name="Fund Center Parent",
    )

    objects = FundCenterManager()

    def __str__(self):
        sn = "No Short name"
        fc = "XXXX"
        if self.fundcenter:
            fc = self.fundcenter.upper()
        if self.shortname:
            sn = self.shortname.upper()
            return f"{fc} - {sn}"
        return ""

    class Meta:
        ordering = ["fundcenter"]
        verbose_name_plural = "Fund Centers"

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "fundcenter",
                    "fundcenter_parent",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]

    def save(self, *args, **kwargs):
        """Saves a FundCenter instance with proper sequence and hierarchy validation.

        This method handles the following operations before saving:
        1. Assigns a new root sequence if no parent is specified
        2. Validates parent-child relationships to prevent self-referencing
        3. Sets the sequence based on parent if valid
        4. Normalizes fundcenter and shortname to uppercase
        5. Calculates hierarchical level based on sequence

        Args:
            *args: Variable length argument list passed to parent save method
            **kwargs: Arbitrary keyword arguments passed to parent save method

        Raises:
            IntegrityError: If a fund center tries to assign itself as its own parent

        Returns:
            None
        """
        if self.fundcenter_parent is None:
            self.sequence = FinancialStructureManager().new_root()
        elif (
            self.fundcenter_parent
            and self.fundcenter == self.fundcenter_parent.fundcenter
        ):
            raise IntegrityError("Children Fund center cannot assign itself as parent")
        elif not FinancialStructureManager().is_child_of(self.fundcenter_parent, self):
            self.sequence = FinancialStructureManager().set_parent(
                self.fundcenter_parent
            )

        self.fundcenter = self.fundcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        self.level = len(self.sequence.split("."))
        super(FundCenter, self).save(*args, **kwargs)

