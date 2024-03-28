from django.db.models import Sum,QuerySet
from bft.models import (
    BftStatusManager,
    CapitalInYear,
    CapitalProject,
    CapitalProjectManager,
    CapitalYearEnd,
    CapitalNewYear,
    FundManager,
    Fund,
)
import pandas as pd


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
        self.layout_margin = dict(l=20, r=20, t=70, b=20)
        self.paper_bgcolor = "LightSteelBlue"


class HistoricalOutlookReport(CapitalReport):
    """This class handles forecasts, spent, initial allocation on annual basis."""

    def __init__(self, fund: str, fy: int, capital_project: str):
        super().__init__(fund, capital_project, fy)
        self.years = list(range(self.fy - 4, self.fy + 1))

    def dataset(self)->dict[QuerySet]:
        in_year = CapitalInYear.objects.filter(
            fund=self.fund, capital_project=self.capital_project, fy__in=self.years
        ).values("fy", "quarter", "mle")
        year_end = CapitalYearEnd.objects.filter(
            fund=self.fund, capital_project=self.capital_project, fy__in=self.years
        ).values("fy", "ye_spent")
        new_year = CapitalNewYear.objects.filter(
            fund=self.fund, capital_project=self.capital_project, fy__in=self.years
        ).values("fy", "initial_allocation")

        return dict(in_year=in_year, new_year=new_year, year_end=year_end)

    def dataframe(self)->int:
        """Create a dataframe of annual data, one row per year for given project and fund"""

        data = self.dataset()
        df = pd.DataFrame()
        if any(data["in_year"]):
            df_in_year = pd.DataFrame.from_dict(data["in_year"])
            df_q1 = df_in_year[df_in_year["quarter"] == "1"]
            df_q1 = df_q1.rename(columns={"mle": "Q1 MLE"})
            df_q1 = df_q1[["Q1 MLE", "fy"]]

            df_q2 = df_in_year[df_in_year["quarter"] == "2"]
            df_q2 = df_q2.rename(columns={"mle": "Q2 MLE"})
            df_q2 = df_q2[["Q2 MLE", "fy"]]

            df_q3 = df_in_year[df_in_year["quarter"] == "3"]
            df_q3 = df_q3.rename(columns={"mle": "Q3 MLE"})
            df_q3 = df_q3[["Q3 MLE", "fy"]]

            df_q4 = df_in_year[df_in_year["quarter"] == "4"]
            df_q4 = df_q4.rename(columns={"mle": "Q4 MLE"})
            df_q4 = df_q4[["Q4 MLE", "fy"]]

            df = df_q1.merge(df_q2, how="left", on="fy")

            if not df_q3.empty:
                df = df.merge(df_q3, how="left", on="fy")
            else:
                df["Q3 MLE"] = 0
            if not df_q4.empty:
                df = df.merge(df_q4, how="left", on="fy")
            else:
                df["Q4 MLE"] = 0

        if any(data["year_end"]):
            df_year_end = pd.DataFrame.from_dict(data["year_end"])
            df = df.merge(df_year_end, how="outer", on="fy")

        if any(data["new_year"]):
            df_new_year = pd.DataFrame.from_dict(data["new_year"])
            print(df_new_year)
            df = df.merge(df_new_year, how="outer", on="fy")

        if not df.empty:
            self.df = df.rename(columns={"ye_spent": "YE Spent", "initial_allocation": "Initial Allocation"})
            self.df = self.df.fillna(0)
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

    def dataset(self)->QuerySet:
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

    def dataframe(self)->int:
        """Create a dataframe of quarterly data, one row per quarter for given fundcenter, fund, and FY"""
        ds=self.dataset()
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
    """This class handles the LE, MLE, and HE of for the Capital Forecasting."""

    def __init__(self, fund: Fund | str, fy: int = None, capital_project: CapitalProject | str = None):
        self.mle = self.he = self.le = []

        super().__init__(fund, capital_project, fy)

    def dataset(self)->QuerySet:
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

    def dataframe(self)->int:
        ds=self.dataset()
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
