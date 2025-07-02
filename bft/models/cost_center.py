import csv

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.db import models
from django.db.models import QuerySet, Sum, Value

from main.settings import UPLOADS
from utils.dataframe import BFTDataFrame

class CostCenterManager(models.Manager):
    """A manager class for handling Cost Center operations and queries in the BFT system.

    This class provides methods to interact with Cost Center objects, including retrieving,
    validating, and transforming cost center data. It handles various operations such as
    checking updatability, generating DataFrames, and managing allocations.

    Methods:
        cost_center(costcenter: str) -> CostCenter|None:
            Retrieves a cost center object by its code.

        pk(pk: int) -> CostCenter|None:
            Retrieves a cost center object by its primary key.

        is_updatable(cc: str|CostCenter) -> bool:
            Checks if a cost center can be updated during DRMIS download.

        has_line_items(costcenter: CostCenter) -> bool:
            Checks if a cost center has associated line items.

        get_sub_alloc(fc: FundCenter|str, fund: Fund|str, fy: int, quarter: int) -> CostCenterAllocation:
            Retrieves cost center allocations for given parameters.

        cost_center_dataframe(data: QuerySet) -> pd.DataFrame:
            Creates a DataFrame of cost centers with financial structure.

        allocation_dataframe(costcenter: CostCenter|str, fund: Fund|str, fy: int, quarter: str) -> pd.DataFrame:
            Creates a DataFrame of cost center allocations.

        forecast_adjustment_dataframe() -> pd.DataFrame:
            Creates a DataFrame of forecast adjustments.

        get_sibblings(parent: FundCenter|str) -> QuerySet:
            Retrieves all cost centers under the same parent.

        exists(costcenter: str) -> bool:
            Checks if a specific cost center or any cost centers exist.

        get_request(request) -> str|None:
            Extracts and validates cost center from an HTTP request.

    Attributes:
        None

    Raises:
        TypeError: When invalid types are provided to methods.
    """
    def cost_center(self, costcenter: str) -> "CostCenter|None":
        """
        Retrieves a CostCenter instance based on the provided cost center code.

        Args:
            costcenter (str): The cost center code to look up.

        Returns:
            CostCenter|None: The matching CostCenter instance if found, None otherwise.
        """
        costcenter = costcenter.upper()
        try:
            cc = CostCenter.objects.get(costcenter=costcenter)
        except CostCenter.DoesNotExist:
            return None
        return cc

    def pk(self, pk: int):
        """
        Retrieves a CostCenter object by its primary key.

        Args:
            pk (int): The primary key of the CostCenter to retrieve.

        Returns:
            CostCenter|None: The CostCenter object if found, None otherwise.
        """
        try:
            cc = CostCenter.objects.get(pk=pk)
        except CostCenter.DoesNotExist:
            return None
        return cc

    def is_updatable(self, cc: "str|CostCenter") -> bool:
        """
        Check if the cost center is updatable during DRMIS download process.
        If not, the cost center will not be affected by the download.

        Args:
            cc (Union[str, CostCenter]): The cost center to check. Can be either a string
                identifier or a CostCenter object.

        Returns:
            bool: True if the cost center is updatable, False otherwise.

        Raises:
            TypeError: If the cost center is neither a string nor a CostCenter object.

        Examples:
            >>> is_updatable("CC001")
            True
            >>> is_updatable(cost_center_obj)
            False
        """
        if isinstance(cc, str):
            cc_: CostCenter = self.cost_center(cc)
            if cc_:
                return cc_.isupdatable
        elif isinstance(cc, CostCenter):
            return cc.isupdatable
        raise TypeError("Cost center of invalid type.")

    def has_line_items(self, costcenter: "CostCenter"):

        return LineItem.objects.filter(costcenter=costcenter).exists()

    def get_sub_alloc(
        self, fc: FundCenter | str, fund: Fund | str, fy: int, quarter: int
    ) -> "CostCenterAllocation":
        """
        Retrieves a CostCenterAllocation object for a given fund center, fund, fiscal year and quarter.

        Args:
            fc (FundCenter | str): The fund center object or fund center code string
            fund (Fund | str): The fund object or fund code string
            fy (int): The fiscal year
            quarter (int): The quarter number (1-4)

        Returns:
            CostCenterAllocation: QuerySet of CostCenterAllocation objects matching the criteria

        Note:
            If string inputs are provided for fc or fund, they will be converted to respective objects
        """
        if isinstance(fc, str):
            fc = FundCenterManager().fundcenter(fc)
        if isinstance(fund, str):
            fund = FundManager().fund(fund)
        cc = FinancialStructureManager().get_fund_center_cost_centers(fc)
        return CostCenterAllocation.objects.filter(
            costcenter__in=cc,
            fy=fy,
            fund=fund,
            quarter=quarter,
        )

    def cost_center_dataframe(self, data: QuerySet) -> pd.DataFrame:
        """
        Create a DataFrame containing cost centers enriched with related fund centers and procurement officers data.

        This method merges cost centers data with fund centers and procurement officers (BftUsers) information
        through left joins. If no cost centers exist in the database, returns an empty DataFrame.

        Args:
            data (QuerySet): QuerySet containing cost center records to process

        Returns:
            pd.DataFrame: DataFrame with merged cost centers, fund centers and procurement officers data.
                         Returns empty DataFrame if no cost centers exist.

        Note:
            - Joins cost centers with fund centers on Costcenter_parent_ID = Fundcenter_ID
            - Joins result with procurement officers on Procurement_officer_ID = Bftuser_ID
            - Logs error if procurement officer merge fails
        """
        if not CostCenter.objects.exists():
            return pd.DataFrame()
        df = BFTDataFrame(CostCenter).build(data)
        fc_df = BFTDataFrame(FundCenter).build(FundCenter.objects.all())
        proco_df = BFTDataFrame(BftUser).build(BftUser.objects.filter(procurement_officer=True))
        df = pd.merge(
            df,
            fc_df,
            how="left",
            left_on="Costcenter_parent_ID",
            right_on="Fundcenter_ID",
        )
        if not proco_df.empty:
            try:
                df = pd.merge(df, proco_df, how="left", left_on="Procurement_officer_ID", right_on="Bftuser_ID")
            except ValueError:
                logger.error("DID not merge cost center dataframe with procurement officer")
        return df

    def allocation_dataframe(
        self,
        costcenter: "CostCenter|str" = None,
        fund: "Fund|str" = None,
        fy: int = None,
        quarter: str = None,
    ) -> pd.DataFrame:
        """
        Returns a DataFrame containing cost center allocation data based on specified filters.

        This method queries CostCenterAllocation records and formats them into a pandas DataFrame
        with renamed columns for better readability.

        Parameters
        ----------
        costcenter : CostCenter or str, optional
            Cost center to filter allocations by. Can be a CostCenter object or cost center code.
        fund : Fund or str, optional
            Fund to filter allocations by. Can be a Fund object or fund code.
        fy : int, optional
            Fiscal year to filter allocations by.
        quarter : str, optional
            Quarter to filter allocations by.

        Returns
        -------
        pd.DataFrame
            DataFrame containing allocation data with the following columns:
            - Fund Center: The fund center code
            - Cost Center: The cost center code
            - Fund: The fund code
            - Allocation: The allocated amount
            - FY: The fiscal year
            - Quarter: The quarter

            Returns empty DataFrame if no matching records are found.
        """
        data = (
            CostCenterAllocation.objects.costcenter(costcenter)
            .fund(fund)
            .fy(fy)
            .quarter(quarter)
        )
        if not data:
            return pd.DataFrame({})
        data = list(
            data.values(
                "costcenter__costcenter_parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
                "fy",
                "quarter",
            )
        )
        columns = {
            "amount": "Allocation",
            "fy": "FY",
            "quarter": "Quarter",
            "costcenter__costcenter": "Cost Center",
            "costcenter__costcenter_parent__fundcenter": "Fund Center",
            "fund__fund": "Fund",
        }
        df = pd.DataFrame(data).rename(columns=columns)
        return df

    def forecast_adjustment_dataframe(self) -> pd.DataFrame:
        """
        Returns a pandas DataFrame containing forecast adjustment data.

        This method retrieves forecast adjustments from the database and formats them into a DataFrame.
        The DataFrame includes Fund Center, Cost Center, Fund and Forecast Adjustment columns.

        Returns:
            pd.DataFrame: A DataFrame containing the following columns:
                - Fund Center: The fund center associated with the cost center
                - Cost Center: The cost center code
                - Fund: The fund code
                - Forecast Adjustment: The adjustment amount

            Returns empty DataFrame if no ForecastAdjustment objects exist.
        """
        if not ForecastAdjustment.objects.exists():
            return pd.DataFrame()
        data = list(
            ForecastAdjustment.objects.all().values(
                "costcenter__costcenter_parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
            )
        )
        columns = {
            "amount": "Forecast Adjustment",
            "costcenter__costcenter_parent__fundcenter": "Fund Center",
            "costcenter__costcenter": "Cost Center",
            "fund__fund": "Fund",
        }
        return pd.DataFrame(data).rename(columns=columns)

    def get_sibblings(self, parent: FundCenter | str):
        """
        Get all sibling cost centers sharing the same parent fund center.

        Args:
            parent (Union[FundCenter, str]): The parent fund center, either as a FundCenter object
                or as a string identifier.

        Returns:
            QuerySet[CostCenter]: QuerySet containing all cost centers that share the specified parent.

        Example:
            >>> fc = FundCenter.objects.get(id='FC001')
            >>> siblings = get_sibblings(fc)
            >>> # Or using string identifier
            >>> siblings = get_sibblings('FC001')
        """
        if isinstance(parent, str):
            parent = FundCenterManager().fundcenter(fundcenter=parent)
        return CostCenter.objects.filter(costcenter_parent=parent)

    def exists(self, costcenter: str = None) -> bool:
        """
        Check if a cost center exists in the database.

        Args:
            costcenter (str, optional): The cost center code to check for. Defaults to None.

        Returns:
            bool: True if the cost center exists, False otherwise.
                  If no costcenter is provided, returns True if any cost centers exist.
        """
        if costcenter:
            return CostCenter.objects.filter(costcenter=costcenter).exists()
        else:
            return CostCenter.objects.count() > 0

    def get_request(self, request) -> str | None:
        """Extract the cost center string from the request and verifies that it exists.

        This method processes a request parameter to extract and validate a cost center code.

        Args:
            request: The HTTP request object containing GET parameters.

        Returns:
            str | None: The uppercase cost center code if it exists and is valid,
                        empty string if the cost center doesn't exist,
                        None if no cost center was provided in the request.

        Examples:
            >>> request.GET = {'costcenter': 'abc123'}
            >>> get_request(request)
            'ABC123'  # if cost center exists

            >>> request.GET = {'costcenter': 'invalid'}
            >>> get_request(request)
            ''  # if cost center doesn't exist

            >>> request.GET = {}
            >>> get_request(request)
            None
        """
        """Extract the cost center string from the request and verifies that it does exist."""
        costcenter = request.GET.get("costcenter")
        if costcenter:
            costcenter = costcenter.upper()
            if not CostCenterManager().exists(costcenter):
                messages.info(request, f"Cost Center {costcenter} does not exist.")
                return ""
            return costcenter
        else:
            return None


class CostCenter(models.Model):
    """A model representing a Cost Center in the financial structure.

    This class represents a Cost Center, which is a financial unit used to track and manage
    expenses and budgets. It includes relationships with Fund and Source models, as well as
    hierarchical relationships with other cost centers through a parent-child structure.

    Attributes:
        costcenter (str): The unique identifier for the cost center (max 6 characters).
        shortname (str): A brief name or description of the cost center (max 35 characters).
        fund (Fund): Foreign key to the Fund model.
        source (Source): Foreign key to the Source model.
        isforecastable (bool): Indicates if forecasting is allowed for this cost center.
        isupdatable (bool): Indicates if updates are allowed for this cost center.
        note (str): Optional text field for additional information.
        sequence (str): Unique path identifier for the cost center hierarchy.
        costcenter_parent (FundCenter): Foreign key to the parent FundCenter.
        procurement_officer (User): Foreign key to the User model for the assigned officer.

    Methods:
        save(*args, **kwargs): Overrides the default save method to ensure proper hierarchy
            and formatting of costcenter and shortname fields.
        __str__(): Returns a string representation of the cost center.

    Meta:
        ordering: Sorts by costcenter field.
        verbose_name_plural: "Cost Centers"
        indexes: Index on costcenter field.
        constraints: Unique constraint on costcenter and costcenter_parent combination.
    """
    costcenter = models.CharField("Cost Center", max_length=6)
    shortname = models.CharField(
        "Cost Center Name", max_length=35, blank=True, null=True
    )
    fund = models.ForeignKey(
        Fund, on_delete=models.RESTRICT, default="", verbose_name="Fund"
    )
    source = models.ForeignKey(
        Source, on_delete=models.RESTRICT, default="", verbose_name="Source"
    )
    isforecastable = models.BooleanField("Is Forecastable", default=False)
    isupdatable = models.BooleanField("Is Updatable", default=False)
    note = models.TextField(null=True, blank=True)
    sequence = models.CharField("CC Path", max_length=25, unique=True, default="")
    costcenter_parent = models.ForeignKey(
        FundCenter,
        on_delete=models.RESTRICT,
        default="0",
        related_name="children",
        verbose_name="Cost Center Parent",
    )
    procurement_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        limit_choices_to={"procurement_officer": True},
    )
    objects = CostCenterManager()

    def __str__(self):
        return f"{self.costcenter.upper()} - {self.shortname}"

    class Meta:
        ordering = ["costcenter"]
        verbose_name_plural = "Cost Centers"
        indexes = [models.Index(fields=["costcenter"])]

        constraints = [
            models.UniqueConstraint(
                fields=(
                    "costcenter",
                    "costcenter_parent",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to handle CostCenter model saving operations.

        This method performs the following operations before saving:
        1. Verifies and sets the parent-child relationship in the financial structure
        2. Converts the costcenter field to uppercase
        3. Converts the shortname field to uppercase (if it exists)

        Args:
            *args: Variable length argument list passed to parent's save method
            **kwargs: Arbitrary keyword arguments passed to parent's save method

        Returns:
            None

        Raises:
            Any exceptions from parent's save method
        """
        if not FinancialStructureManager().is_child_of(self.costcenter_parent, self):
            self.sequence = FinancialStructureManager().set_parent(
                self.costcenter_parent, costcenter_child=True
            )

        self.costcenter = self.costcenter.upper()
        if self.shortname:
            self.shortname = self.shortname.upper()
        super(CostCenter, self).save(*args, **kwargs)


class CostCenterChargeImport(models.Model):
    """This class defines the model that represents the DND Actual Listings, Cost Center Transaction Listing report.
    Historically known as Charges against cost center. Each line read from the report during the uploadcsv command must match this model.

    This table contains charges for the current fiscal year only. Its content is to be deleted when moving to a new FY.

    Sample report format:

    Attributes:
        fund (CharField): Fund code, max 4 chars
        costcenter (CharField): Cost center code, max 6 chars
        gl (CharField): General ledger code, max 5 chars
        ref_doc_no (CharField): Reference document number, max 10 chars
        aux_acct_asmnt (CharField): Auxiliary account assessment, max 20 chars
        amount (DecimalField): Transaction amount with 2 decimal places
        doc_type (CharField): Document type code, max 2 chars, optional
        posting_date (DateField): Date when transaction was posted
        period (CharField): Accounting period, max 2 chars
        fy (PositiveSmallIntegerField): Fiscal year of the transaction

    Here is a sample report with its header and ons single line:
    |Fund|Cost Ctr|Cost Elem.|RefDocNo  |AuxAcctAsmnt_1  |    ValCOArCur|DocTyp|Postg Date|Per|
    -------------------------------------------------------------------------------------------
    |L111|46722A  |1101      |7000008167|ORD 11189281    |     1,273.38-|RX    |2023.10.17|  7|
    """

    fund = models.CharField(max_length=4)
    costcenter = models.CharField(max_length=6)
    gl = models.CharField(max_length=5)
    ref_doc_no = models.CharField(max_length=10)
    aux_acct_asmnt = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    doc_type = models.CharField(max_length=2, null=True, blank=True)
    posting_date = models.DateField()
    period = models.CharField(max_length=2)
    fy = models.PositiveSmallIntegerField("Fiscal Year", default=0)


class CostCenterChargeMonthlyManager(models.Manager):
    """A manager class for CostCenterChargeMonthly model operations.

    This manager handles monthly cost center charge operations including flushing
    and inserting records for specified fiscal years and periods.

    Methods:
        flush_current() -> int:
            Deletes all records for the current fiscal year and period.
            Returns number of deleted records.

        flush_monthly(fy: int, period: str) -> int:
            Deletes all records for a specified fiscal year and period.
            Args:
                fy: Fiscal year
                period: Period string
            Returns number of deleted records.

        insert_current(fy, period) -> int:
            Inserts aggregated records from CostCenterChargeImport into monthly table.
            Args:
                fy: Fiscal year
                period: Period to aggregate up to
            Returns number of inserted records.
    """
    def flush_current(self) -> int:
        """
        Deletes all CostCenterChargeMonthly records for the current fiscal year and period.

        Returns:
            int: Number of records deleted
        """
        fy = BftStatusManager().fy()
        period = BftStatusManager().period()
        res = CostCenterChargeMonthly.objects.filter(fy=fy, period=period).delete()
        return res[0]

    def flush_monthly(self, fy: int, period: str) -> int:
        """
        Deletes all monthly cost center charges for a specific fiscal year and period.

        Args:
            fy (int): The fiscal year to flush charges for
            period (str): The period (month) to flush charges for

        Returns:
            int: Number of records deleted from the database
        """

        res = CostCenterChargeMonthly.objects.filter(fy=fy, period=period).delete()
        return res[0]

    def insert_current(self, fy, period) -> int:
        """
        Insert cost center charges into monthly table for given fiscal year and period.

        This method aggregates cost center charge imports up to the specified period and
        creates monthly summary records.

        Args:
            fy (int): Fiscal year to process
            period (int): Period number within fiscal year (1-12)

        Returns:
            int: Number of records inserted into cost_center_charge_monthly table
        """
        current = (
            CostCenterChargeImport.objects.filter(fy=fy, period__lte=period)
            .values("costcenter", "fund", "fy")
            .annotate(amount=Sum("amount"), period=Value(period))
        )
        lines = CostCenterChargeMonthly.objects.bulk_create(
            [CostCenterChargeMonthly(**c) for c in current]
        )
        linecount = len(lines)
        logger.info(f"Inserted {linecount} in table cost_center_charge_monthly")
        return linecount


class CostCenterChargeMonthly(models.Model):
    """A Django model representing monthly charges for cost centers.
    This model stores the monthly financial charges associated with specific cost centers,
    including fund information, cost center details, charge amounts, and fiscal period data.
    Attributes:
        fund (CharField): A 4-character field representing the fund code.
        costcenter (CharField): A 6-character field representing the cost center identifier.
        amount (DecimalField): The monetary amount charged, with up to 10 digits and 2 decimal places.
        period (CharField): A 2-character field representing the period (typically month).
        fy (PositiveSmallIntegerField): The fiscal year associated with the charge.
    Meta:
        verbose_name_plural: "Cost Center charges monthly"
    """

    fund = models.CharField(max_length=4)
    costcenter = models.CharField("Cost Center", max_length=6)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    period = models.CharField(max_length=2)
    fy = models.PositiveSmallIntegerField("Fiscal Year", default=0)

    objects = CostCenterChargeMonthlyManager()

    def __str__(self):
        return f"{self.fund} {self.costcenter} {self.amount} {self.fy} {self.period}"

    class Meta:
        verbose_name_plural = "Cost Center charges monthly"


class CostCenterChargeProcessor:
    """Process and manage cost center charges from CSV files and database operations.

    This class handles the processing of cost center charges, including CSV file operations,
    database imports, and monthly charge management.

    Attributes:
        csv_file (str): Path to the charges CSV file in the uploads directory.
        fy (str): Current fiscal year obtained from BftStatusManager.

    Methods:
        to_csv(source_file: str, period: str):
            Processes a source CSV file with cost center charges and saves it in a standardized format.
            Performs data cleaning, format validation and period checking.

        csv2cost_center_charge_import_table(fy: str, period: str):
            Imports processed CSV data into the CostCenterChargeImport database table.
            Deletes existing records for the given fiscal year and period before import.

        monthly_charges(fy: str, period: str) -> int:
            Manages monthly charges using CostCenterChargeMonthlyManager.
            Flushes existing monthly data and inserts current period charges.
            Returns the number of processed records.

    Raises:
        ValueError: If period validation fails during CSV processing.
    """

    def __init__(self):
        self.csv_file = f"{UPLOADS}/charges.csv"
        self.fy = BftStatusManager().fy()

    def to_csv(self, source_file: str, period: str):
        """
        Converts a BFT source file to CSV format with specific data transformations.

        This method reads a BFT source file, performs various data cleansing and formatting operations,
        and saves the result as a CSV file. The process includes:
        - Reading the source file with specific column datatypes and formatting
        - Removing empty rows
        - Stripping whitespace from all columns
        - Formatting dates
        - Handling currency values and negative signs
        - Adding fiscal year information
        - Validating period consistency

        Args:
            source_file (str): Path to the source BFT file to be converted
            period (str): The accounting period to validate against the file contents

        Raises:
            ValueError: If multiple periods are found in the file or if the specified period
                       doesn't match the period in the file

        Returns:
            None: The processed data is saved to self.csv_file

        Note:
            The source file is expected to be pipe-delimited (|) with specific column structure
            and the output will be saved to the location specified in self.csv_file
        """

        df = pd.read_csv(
            source_file,
            dtype={2: object, 3: object, 8: object},
            sep="|",
            header=3,
            usecols=list(range(1, 10)),
            skipfooter=1,
            skipinitialspace=True,
            index_col=False,
            engine="python",
        )

        # flush empty lines
        df = df[df["Fund"].notnull()]

        # Strip white spaces
        for col in df.columns:
            try:
                df[col] = df[col].str.strip()
            except AttributeError:
                pass

        # format date
        df["Postg Date"] = pd.to_datetime(df["Postg Date"], format="%Y.%m.%d")

        # strip , character from  ValCOArCur
        df["ValCOArCur"] = df["ValCOArCur"].str.replace(",", "")

        # move negative sign forward
        df.loc[df["ValCOArCur"].str.endswith("-"), "ValCOArCur"] = "-" + df[
            "ValCOArCur"
        ].str.replace("-", "")

        # set FY
        df["fy"] = self.fy

        # Confirm we have one single period
        periods = df["Per"].to_numpy()
        all_same = (periods[0] == periods).all()
        if not all_same:
            raise ValueError("element values in periods are not all the same")

        # Confirm period passed to command line matches those of csv file
        if periods[0] != period:
            raise ValueError(
                f"Requested period {period} does not match the periods in the file"
            )

        df.to_csv(self.csv_file, index=False)

    def csv2cost_center_charge_import_table(self, fy, period):
        """
        Import cost center charges from a CSV file into the CostCenterChargeImport table.

        First deletes any existing records for the given fiscal year and period, then reads the CSV file
        line by line to create new CostCenterChargeImport records.

        The CSV file must have the following columns in order:
        fund, costcenter, gl, ref_doc_no, aux_acct_asmnt, amount, doc_type, posting_date, period, fy

        Args:
            fy (str): Fiscal year for the imported charges
            period (str): Period for the imported charges

        Note:
            The CSV file must be previously set as self.csv_file
            The first row of the CSV file is assumed to be a header and is skipped

        Returns:
            None
        """
        CostCenterChargeImport.objects.filter(fy=fy, period=period).delete()
        with open(self.csv_file) as file:
            next(file)  # skip the header row
            reader = csv.reader(file)
            for row in reader:
                charge_line = CostCenterChargeImport(
                    fund=row[0],
                    costcenter=row[1],
                    gl=row[2],
                    ref_doc_no=row[3],
                    aux_acct_asmnt=row[4],
                    amount=row[5],
                    doc_type=row[6],
                    posting_date=row[7],
                    period=row[8],
                    fy=row[9],
                )
                charge_line.save()

    def monthly_charges(self, fy, period) -> int:
        """
        Generate and insert monthly charges for a specific fiscal year and period.

        This method flushes existing monthly charges and inserts new ones using
        the CostCenterChargeMonthlyManager.

        Args:
            fy (int): Fiscal year for the charges
            period (int): Period number within the fiscal year (1-12)

        Returns:
            int: Number of monthly charge records inserted

        Raises:
            None
        """
        m = CostCenterChargeMonthlyManager()
        m.flush_monthly(fy, period)
        return m.insert_current(fy, period)
