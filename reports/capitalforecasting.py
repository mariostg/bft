import pandas as pd
from django.db.models import QuerySet, Sum

from bft.models import (BftStatusManager, CapitalInYear, CapitalNewYear,
                        CapitalProject, CapitalProjectManager, CapitalYearEnd,
                        Fund, FundManager)


class CapitalReport:
    """A class for generating capital project financial reports.

    This class handles the creation and management of capital project reports,
    including data processing and visualization components.

    Parameters
    ----------
    fund : str
        The fund identifier for the capital project
    capital_project : str
        The identifier for the specific capital project
    fy : int, optional
        The fiscal year for the report. If not provided, uses current fiscal year

    Attributes
    ----------
    _dataset : None
        Placeholder for dataset
    df : pandas.DataFrame
        Main dataframe for storing report data
    quarters : list
        List of fiscal quarters [1,2,3,4]
    fy : int
        Fiscal year for the report
    capital_project : CapitalProject
        The capital project object being reported on
    fund : Fund
        The fund object associated with the project
    chart_width : int
        Width in pixels for chart visualizations
    layout_margin : dict
        Margin settings for chart layouts
    paper_bgcolor : str
        Background color for charts/reports
    """
    def __init__(self, fund: str, capital_project: str, fy: int):
        self._dataset = None
        self.df = pd.DataFrame()
        self.quarters = [1, 2, 3, 4]
        if not fy:
            self.fy = BftStatusManager().fy()
        else:
            self.fy = fy
        self.capital_project = CapitalProjectManager().project(capital_project)

        self.fund = FundManager().fund(fund)
        self.chart_width = 400
        self.layout_margin = {"l": 20, "r": 20, "t": 70, "b": 20}
        self.paper_bgcolor = "LightSteelBlue"


class HistoricalOutlookReport(CapitalReport):
    """A class for generating historical capital forecast reports.

    This class handles the creation and presentation of historical capital forecast data,
    including initial allocations, quarterly Most Likely Estimates (MLE), and year-end spent amounts
    over a 5-year period (current fiscal year and 4 previous years).

    Args:
        fund (str): The fund identifier.
        fy (int): The fiscal year.
        capital_project (str): The capital project identifier.

    Attributes:
        years (list): List of fiscal years to include in report (fy-4 to fy).
        df (pandas.DataFrame): DataFrame containing the formatted report data.

    Example:
        >>> report = HistoricalOutlookReport('FUND1', 2023, 'PROJECT1')
        >>> report.dataframe()
        >>> html_output = report.to_html()

    Notes:
        - Inherits from CapitalReport base class
        - Retrieves data from CapitalInYear, CapitalYearEnd, and CapitalNewYear models
        - Formats monetary values as integers with thousand separators in HTML output
    """

    def __init__(self, fund: str, fy: int, capital_project: str):
        super().__init__(fund, capital_project, fy)
        self.years = list(range(self.fy - 4, self.fy + 1))

    def dataset(self) -> dict[str, QuerySet]:
        """This method queries three different capital-related models to create a comprehensive
        dataset of capital information based on the instance's fund, capital project, and years.

        Returns:
            dict[str, QuerySet]: A dictionary containing three QuerySets:
                - 'in_year': CapitalInYear records with fy, quarter, and mle values
                - 'year_end': CapitalYearEnd records with fy and ye_spent values
                - 'new_year': CapitalNewYear records with fy and initial_allocation values
                All QuerySets are ordered by fiscal year (and quarter where applicable)
        """
        base_filters = {"fund": self.fund, "capital_project": self.capital_project, "fy__in": self.years}

        return {
            "in_year": CapitalInYear.objects.filter(**base_filters)
            .values("fy", "quarter", "mle")
            .order_by("fy", "quarter"),
            "year_end": CapitalYearEnd.objects.filter(**base_filters).values("fy", "ye_spent").order_by("fy"),
            "new_year": CapitalNewYear.objects.filter(**base_filters)
            .values("fy", "initial_allocation")
            .order_by("fy"),
        }

    def dataframe(self) -> int:
        """
        Processes and transforms capital forecasting data into a structured DataFrame.

        This method combines various financial data points including quarterly MLE (Most Likely Estimate),
        year-end spent amounts, and initial allocations into a single DataFrame.

        Returns:
            int: The size of the resulting DataFrame (number of elements).

        Notes:
            - Processes quarterly MLE data through pivot operations
            - Handles year-end spent amounts and initial allocations through merge operations
            - Fills missing values with zeros
            - Updates the instance DataFrame (self.df) with the processed data

        The resulting DataFrame contains the following columns when data is available:
            - fy: Fiscal Year
            - Q1 MLE, Q2 MLE, Q3 MLE, Q4 MLE: Quarterly Most Likely Estimates
            - YE Spent: Year End spent amounts
            - Initial Allocation: New year initial allocations
        """
        data = self.dataset()
        df = pd.DataFrame()

        if any(data["in_year"]):
            df_in_year = pd.DataFrame.from_dict(data["in_year"])
            # Convert all quarters at once using pivot
            df = (
                df_in_year.pivot(index="fy", columns="quarter", values="mle")
                .rename(columns={"1": "Q1 MLE", "2": "Q2 MLE", "3": "Q3 MLE", "4": "Q4 MLE"})
                .reset_index()
            )

            # Fill NaN values with 0
            mle_columns = ["Q1 MLE", "Q2 MLE", "Q3 MLE", "Q4 MLE"]
            df[mle_columns] = df[mle_columns].fillna(0)

        # Merge year_end and new_year data
        for key, column_map in [
            ("year_end", {"ye_spent": "YE Spent"}),
            ("new_year", {"initial_allocation": "Initial Allocation"}),
        ]:
            if any(data[key]):
                temp_df = pd.DataFrame.from_dict(data[key])
                df = df.merge(temp_df, how="outer", on="fy")
                df = df.rename(columns=column_map)

        if not df.empty:
            self.df = df.fillna(0)

        return self.df.size

    def to_html(self):
        """
        Converts the current dataframe to an HTML representation with formatted numeric columns.

        Returns:
            str: HTML string representation of the dataframe with formatted numbers.
                Returns "Dataframe is empty." if the dataframe has no data.
                Numbers in specific columns are formatted with thousands separators and no decimals.

        Formatted columns:
            - Initial Allocation
            - Q1 MLE
            - Q2 MLE
            - Q3 MLE
            - Q4 MLE
            - YE Spent

        Note:
            This method calls dataframe() internally before converting to HTML.
        """
        self.dataframe()
        if self.df.empty:
            return "Dataframe is empty."
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["Initial Allocation", "Q1 MLE", "Q2 MLE", "Q3 MLE", "Q4 MLE", "YE Spent"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )


class FEARStatusReport(CapitalReport):
    """FEAR (Forecasting, Encumbrance, Allocation Relationship) Status report.

    This class handles quarterly financial data for capital projects, generating reports with forecasting,
    encumbrance and allocation relationships.

    Args:
        fund (str): The fund identifier
        fy (int, optional): Fiscal year. Defaults to None.
        capital_project (str, optional): Capital project identifier. Defaults to None.

    Attributes:
        quarters (list): List of quarters [1,2,3,4]
        df (pandas.DataFrame): Dataframe storing the quarterly financial data

    Methods:
        dataset(): Returns a QuerySet with aggregated quarterly financial data
        dataframe(): Creates a pandas DataFrame from the dataset
        to_html(): Renders the dataframe as formatted HTML table

    Inherits From:
        CapitalReport

    Example:
        >>> report = FEARStatusReport('ABC123', 2023, 'PRJ01')
        >>> report.dataframe()
        >>> print(report.to_html())
    """
    """FEAR (Forecasting, Encumbrance, Allocation Relationship) Status report. This class handles all quarter related fields"""

    def __init__(self, fund: str, fy: int = None, capital_project: str = None):
        """Initialize capital forecast report class.

        Args:
            fund (str): Fund identifier.
            fy (int, optional): Fiscal year. Defaults to None.
            capital_project (str, optional): Capital project identifier. Defaults to None.

        Note:
            Sets up quarters list [1,2,3,4] and calls parent class initialization.
        """
        self.quarters = [1, 2, 3, 4]
        super().__init__(fund, capital_project, fy)

    def dataset(self) -> QuerySet:
        """
        Retrieves and aggregates capital forecasting data for a specific fiscal year, fund, and capital project.

        Returns:
            QuerySet: A queryset containing aggregated capital data with the following annotations:
                - MLE: Sum of 'mle' (Most Likely Estimate)
                - LE: Sum of 'le' (Low Estimate)
                - HE: Sum of 'he' (High Estimate)
                - CO: Sum of 'co' (Carry Over)
                - PC: Sum of 'pc' (Project Completion)
                - FR: Sum of 'fr' (Future Requirements)
                - Spent: Sum of actual spent amounts
                - allocation: Sum of allocated amounts

            The queryset is grouped and ordered by capital_project, fund, and quarter.
        """
        return (
            CapitalInYear.objects.filter(fy=self.fy, fund=self.fund, capital_project=self.capital_project)
            .values("capital_project", "fund", "quarter")
            .order_by("capital_project", "fund", "quarter")
            .annotate(
                MLE=Sum("mle"),
                LE=Sum("le"),
                HE=Sum("he"),
                CO=Sum("co"),
                PC=Sum("pc"),
                FR=Sum("fr"),
                Spent=Sum("spent"),
                allocation=Sum("allocation"),
            )
        )

    def dataframe(self) -> int:
        """
        Creates a pandas DataFrame from the dataset containing quarterly financial data.
        The 'quarter' column is renamed to 'Quarters' in the resulting DataFrame.

        Returns:
            int: Size of the resulting DataFrame, or 0 if dataset is empty

        Side Effects:
            Sets self.df with the created pandas DataFrame
        """

        ds = self.dataset()
        if not ds.count():
            return 0
        self.df = pd.DataFrame.from_dict(ds)
        self.df.rename(columns={"quarter": "Quarters"}, inplace=True)
        return self.df.size

    def to_html(self):
        """Converts the capital forecast data into HTML format.

        This method first generates the dataframe using the dataframe() method and then
        converts it to HTML with specific number formatting for financial values.

        Returns:
            str: HTML representation of the dataframe with financial numbers formatted
                 without decimals and with thousand separators.
                 Returns "Dataframe is empty." if the dataframe has no data.

        Note:
            Applies formatting to the following columns if they exist:
            - allocation
            - forecast
            - le (lower estimate)
            - he (higher estimate)
            - co (carry over)
            - pc (project cost)
            - fr (forecast)
        """
        self.dataframe()
        if self.df.empty:
            return "Dataframe is empty."
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["allocation", "forecast", "le", "he", "forecast", "co", "pc", "fr"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )


class EncumbranceStatusReport(CapitalReport):
    """A Capital Report that shows encumbrance status for a given fund, fiscal year, and quarter.

    This report aggregates capital spending data including commitments (CO), pre-commitments (PC),
    funds reservations (FR) and actual spent amounts for capital projects.

    Parameters
    ----------
    fund : Fund or str
        The fund to generate the report for
    fy : int
        The fiscal year
    quarter : int
        The quarter (1-4)
    capital_project : CapitalProject or str, optional
        Specific capital project to filter by (default is None)

    Attributes
    ----------
    spent : float
        Total spent amount
    co : float
        Total commitments
    pc : float
        Total pre-commitments
    fr : float
        Total funds reservations
    quarter : int
        Report quarter
    df : pandas.DataFrame
        The report data in DataFrame format

    Methods
    -------
    dataset()
        Returns queryset of aggregated capital spending data
    dataframe()
        Converts dataset to pandas DataFrame
    to_html()
        Renders report as HTML table with formatted numbers
    """
    def __init__(self, fund: Fund | str, fy: int, quarter: int, capital_project: CapitalProject | str = None):
        self.spent = self.co = self.pc = self.fr = 0
        self.quarter = quarter

        super().__init__(fund, capital_project, fy)

    def dataset(self):
        """
        Retrieves aggregated capital forecasting data for a specific fiscal year, fund, and quarter.

        The method performs a database query on CapitalInYear objects, filtering by fiscal year,
        fund, and quarter. It groups and aggregates financial data by capital project details.

        Returns:
            QuerySet: A queryset containing dictionaries with the following structure:
                - capital_project: The capital project identifier
                - fund: The fund identifier
                - quarter: The quarter number
                - capital_project__project_no: The project number
                - capital_project__fundcenter__fundcenter: The fund center identifier
                - CO: Sum of carry over amounts
                - PC: Sum of project costs
                - FR: Sum of forecast amounts
                - Spent: Sum of spent amounts

        The results are ordered by capital project, fund, quarter, project number, and fund center.
        """
        return (
            CapitalInYear.objects.filter(fy=self.fy, fund=self.fund, quarter=self.quarter)
            .values(
                "capital_project",
                "fund",
                "quarter",
                "capital_project__project_no",
                "capital_project__fundcenter__fundcenter",
            )
            .order_by(
                "capital_project",
                "fund",
                "quarter",
                "capital_project__project_no",
                "capital_project__fundcenter__fundcenter",
            )
            .annotate(
                CO=Sum("co"),
                PC=Sum("pc"),
                FR=Sum("fr"),
                Spent=Sum("spent"),
            )
        )

    def dataframe(self):
        """
        Converts dataset into a pandas DataFrame with column renaming.

        Returns:
            pd.DataFrame: DataFrame containing capital project data with renamed columns:
                - 'capital_project__fundcenter__fundcenter' renamed to 'Fund Center'
                - 'capital_project__project_no' renamed to 'Project No'
        """
        self.df = pd.DataFrame.from_dict(self.dataset()).rename(
            columns={
                "capital_project__fundcenter__fundcenter": "Fund Center",
                "capital_project__project_no": "Project No",
            }
        )

    def to_html(self):
        """Convert the report data to an HTML table representation.

        Returns:
            str: HTML table representation of the data. Each numeric column (CO, PC, FR, Spent)
                 will be formatted with thousands separators and no decimal places.
                 Returns "Dataframe is empty." if the underlying dataframe has no data.

        Notes:
            - Calls dataframe() method internally to ensure data is loaded
            - Formats numeric columns using "{:,.0f}" format string
            - Affected columns: CO (Carry Over), PC (Purchase Commitment),
              FR (Fund Reservation), Spent
        """
        self.dataframe()
        if self.df.empty:
            return "Dataframe is empty."
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["CO", "PC", "FR", "Spent"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )


class EstimateReport(CapitalReport):
    """A class to generate capital reports with Low Estimate (LE), Most Likely Estimate (MLE), and High Estimate (HE).

    This class inherits from CapitalReport and handles the creation of reports containing various estimates
    for capital forecasting purposes. It processes data from CapitalInYear objects and can output HTML formatted reports.

    Parameters
    ----------
    fund : Fund or str
        The fund to generate the report for
    fy : int, optional
        The fiscal year for the report (default is None)
    capital_project : CapitalProject or str, optional
        The specific capital project to report on (default is None)

    Attributes
    ----------
    mle : list
        Most Likely Estimate data
    he : list
        High Estimate data
    le : list
        Low Estimate data
    df : pandas.DataFrame
        DataFrame containing the processed report data

    Methods
    -------
    dataset()
        Retrieves and processes the QuerySet for capital estimates
    dataframe()
        Converts the dataset into a pandas DataFrame
    to_html()
        Generates an HTML representation of the report

    Returns
    -------
    Various return types depending on the method called:
        - dataset(): Django QuerySet
        - dataframe(): int (size of DataFrame)
        - to_html(): str (HTML formatted string)
    """
    """This class handles the LE, MLE, and HE of for the Capital Forecasting."""

    def __init__(self, fund: Fund | str, fy: int = None, capital_project: CapitalProject | str = None):
        self.mle = self.he = self.le = []

        super().__init__(fund, capital_project, fy)

    def dataset(self) -> QuerySet:
        """
        Retrieves and aggregates capital project financial data for a specific fiscal year, fund, and project.

        Returns:
            QuerySet: A Django QuerySet containing aggregated financial data with the following fields:
                - capital_project: The capital project identifier
                - fund: The fund identifier
                - quarter: The fiscal quarter
                - capital_project__project_no: The project number
                - capital_project__fundcenter__fundcenter: The fund center identifier
                - MLE: Sum of Most Likely Estimate values
                - LE: Sum of Low Estimate values
                - HE: Sum of High Estimate values
                - working_plan: Sum of spent + carried over + pre-committed + future requirements

        The results are ordered by capital project, fund, quarter, project number, and fund center.
        """
        return (
            CapitalInYear.objects.filter(fy=self.fy, fund=self.fund, capital_project=self.capital_project)
            .values(
                "capital_project",
                "fund",
                "quarter",
                "capital_project__project_no",
                "capital_project__fundcenter__fundcenter",
            )
            .order_by(
                "capital_project",
                "fund",
                "quarter",
                "capital_project__project_no",
                "capital_project__fundcenter__fundcenter",
            )
            .annotate(
                MLE=Sum("mle"),
                LE=Sum("le"),
                HE=Sum("he"),
                working_plan=Sum("spent") + Sum("co") + Sum("pc") + Sum("fr"),
            )
        )

    def dataframe(self) -> int:
        """
        Creates and processes a pandas DataFrame from the dataset.

        This method transforms the dataset into a DataFrame and renames specific columns
        for better readability. The columns renamed are:
        - 'capital_project__fundcenter__fundcenter' to 'Fund Center'
        - 'capital_project__project_no' to 'Project No'
        - 'working_plan' to 'Working Plan'

        Returns:
            int: The size of the resulting DataFrame, or 0 if the dataset is empty
        """
        ds = self.dataset()
        if not ds.count():
            return 0
        self.df = pd.DataFrame.from_dict(ds).rename(
            columns={
                "capital_project__fundcenter__fundcenter": "Fund Center",
                "capital_project__project_no": "Project No",
                "working_plan": "Working Plan",
            }
        )
        return self.df.size

    def to_html(self):
        """
        Converts the capital forecasting data to an HTML representation.

        This method first generates the dataframe using the dataframe() method, then
        formats the numerical columns (MLE, HE, LE, working_plan) to display as integers
        with thousand separators before converting to HTML.

        Returns:
            str: HTML string representation of the dataframe. If the dataframe is empty,
                 returns the message "Dataframe is empty."

        Note:
            The following columns are formatted with thousand separators:
            - MLE (Most Likely Estimate)
            - HE (High Estimate)
            - LE (Low Estimate)
            - working_plan
        """
        self.dataframe()
        if self.df.empty:
            return "Dataframe is empty."
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["MLE", "HE", "LE", "working_plan"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )
