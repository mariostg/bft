import pandas as pd
from django.db.models import QuerySet, Sum

from bft.models import (BftStatusManager, CapitalInYear, CapitalNewYear,
                        CapitalProject, CapitalProjectManager, CapitalYearEnd,
                        Fund, FundManager)


class CapitalReport:
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
    """This class handles forecasts, spent, initial allocation on annual basis."""

    def __init__(self, fund: str, fy: int, capital_project: str):
        super().__init__(fund, capital_project, fy)
        self.years = list(range(self.fy - 4, self.fy + 1))

    def dataset(self) -> dict[str, QuerySet]:
        """
        Retrieves capital data for the given fund, project and years.
        Returns a dictionary containing in_year, year_end, and new_year QuerySets.
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
        """Create a dataframe of annual data, one row per year for given project and fund"""
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
    """This class handles all quarter related fields"""

    def __init__(self, fund: str, fy: int = None, capital_project: str = None):
        self.quarters = [1, 2, 3, 4]
        super().__init__(fund, capital_project, fy)

    def dataset(self) -> QuerySet:
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
        """Create a dataframe of quarterly data, one row per quarter for given fundcenter, fund, and FY"""
        ds = self.dataset()
        if not ds.count():
            return 0
        self.df = pd.DataFrame.from_dict(ds)
        self.df.rename(columns={"quarter": "Quarters"}, inplace=True)
        return self.df.size

    def to_html(self):
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
    def __init__(self, fund: Fund | str, fy: int, quarter: int, capital_project: CapitalProject | str = None):
        self.spent = self.co = self.pc = self.fr = 0
        self.quarter = quarter

        super().__init__(fund, capital_project, fy)

    def dataset(self):
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
        self.df = pd.DataFrame.from_dict(self.dataset()).rename(
            columns={
                "capital_project__fundcenter__fundcenter": "Fund Center",
                "capital_project__project_no": "Project No",
            }
        )

    def to_html(self):
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
