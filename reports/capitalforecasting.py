from django.db.models import Sum
from costcenter.models import CapitalForecasting, CapitalProject, FundCenterManager, FundManager
from bft.models import BftStatusManager
import pandas as pd
import plotly.express as px
from main import settings


class CapitalReport:
    def __init__(self, fundcenter: str, fund: str, capital_project: str):
        self._dataset = None
        self.df = pd.DataFrame()
        if capital_project:
            try:
                self.capital_project = CapitalProject.objects.get(project_no=capital_project)
            except CapitalProject.DoesNotExist:
                return None
        self.fundcenter = FundCenterManager().fundcenter(fundcenter)
        self.fund = FundManager().fund(fund)


class HistoricalOutlookReport(CapitalReport):
    """This class handles forecasts, spent, initial allocation on annual basis."""

    def __init__(self, fundcenter: str, fund: str, capital_project: str):
        super().__init__(fundcenter, fund, capital_project)

    def dataset(self):
        return (
            CapitalForecasting.objects.filter(fundcenter=self.fundcenter)
            .values("fy")
            .annotate(
                initial_allocation=Sum("initial_allocation"),
                q1_forecast=Sum("q1_forecast"),
                q2_forecast=Sum("q2_forecast"),
                q3_forecast=Sum("q3_forecast"),
                ye_spent=Sum("ye_spent"),
            )
        )

    def dataframe(self):
        """Create a dataframe of annual data, one row per year for given fundcenter, project and fund"""
        self.df = pd.DataFrame.from_dict(self.dataset())

    def to_html(self):
        self.dataframe()
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["initial_allocation", "q1_forecast", "q2_forecast", "q3_forecast", "ye_spent"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )

    def chart(self):
        return px.bar(
            self.df,
            x="fy",
            y=["initial_allocation", "q1_forecast", "q2_forecast", "q3_forecast", "ye_spent"],
            title=f"historical outlook <br><sup>{self.capital_project}, {self.fund.fund}</sup>",
            height=300,
            barmode="group",
        )


class QuarterReport(CapitalReport):
    """This class handles all quarter related fields"""

    def __init__(self, fundcenter: str, fund: str, fy: int = None, capital_project: str = None):
        self.quarters = [1, 2, 3, 4]
        if not fy:
            self.fy = BftStatusManager().fy()
        else:
            self.fy = fy
        super().__init__(fundcenter, fund, capital_project)

    def dataset(self, quarter: int):
        return (
            CapitalForecasting.objects.filter(
                fy=self.fy,
                fundcenter=self.fundcenter,
                fund=self.fund,
                capital_project=self.capital_project,
            )
            .values("fy")
            .annotate(
                allocation=Sum(f"q{quarter}_allocation"),
                forecast=Sum(f"q{quarter}_forecast"),
                le=Sum(f"q{quarter}_le"),
                he=Sum(f"q{quarter}_he"),
                spent=Sum(f"q{quarter}_spent"),
                co=Sum(f"q{quarter}_co"),
                pc=Sum(f"q{quarter}_pc"),
                fr=Sum(f"q{quarter}_fr"),
            )
        )

    def dataframe(self):
        """Create a dataframe of quarterly data, one row per quarter for given fundcenter, fund, and FY"""
        self.df = pd.DataFrame()
        for q in [1, 2, 3, 4]:
            df = pd.DataFrame.from_dict(self.dataset(q))
            df["Quarter"] = q
            self.df = pd.concat([self.df, df])
        self.df = self.df.set_index(["Quarter"])

    def to_html(self):
        self.dataframe()
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["allocation", "forecast", "le", "he", "forecast", "co", "pc", "fr"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )


class EstimateReport(CapitalReport):
    """This class handles the LE, MLE, and HE of for the Capital Forecasting."""

    def __init__(self, fundcenter: str, fund: str, fy: int = None, capital_project: str = None):
        self.mle = self.he = self.le = []
        self.quarters = [1, 2, 3, 4]
        if not fy:
            self.fy = BftStatusManager().fy()
        else:
            self.fy = fy
        super().__init__(fundcenter, fund, capital_project)

    def dataset(self):
        return (
            CapitalForecasting.objects.filter(fy=self.fy, fundcenter=self.fundcenter, fund=self.fund)
            .values("fundcenter", "fund", "fy")
            .annotate(
                Q1_MLE=Sum("q1_forecast"),
                Q2_MLE=Sum("q2_forecast"),
                Q3_MLE=Sum("q3_forecast"),
                Q4_MLE=Sum("q4_forecast"),
                Q1_LE=Sum("q1_le"),
                Q2_LE=Sum("q2_le"),
                Q3_LE=Sum("q3_le"),
                Q4_LE=Sum("q4_le"),
                Q1_HE=Sum("q1_he"),
                Q2_HE=Sum("q2_he"),
                Q3_HE=Sum("q3_he"),
                Q4_HE=Sum("q4_he"),
            )
        )[0]

    def quarterly(self):
        _dataset = self.dataset()
        self.mle = [
            _dataset["Q1_MLE"],
            _dataset["Q2_MLE"],
            _dataset["Q3_MLE"],
            _dataset["Q4_MLE"],
        ]
        self.le = [
            _dataset["Q1_LE"],
            _dataset["Q2_LE"],
            _dataset["Q3_LE"],
            _dataset["Q4_LE"],
        ]
        self.he = [
            _dataset["Q1_HE"],
            _dataset["Q2_HE"],
            _dataset["Q3_HE"],
            _dataset["Q4_HE"],
        ]

    def dataframe(self):
        self.dataset()
        self.quarterly()
        self.df = pd.DataFrame({"Quarters": self.quarters, "MLE": self.mle, "HE": self.he, "LE": self.le})

    def to_html(self):
        self.dataframe()
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["MLE", "HE", "LE"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )

    def chart(self):
        return px.bar(
            self.df,
            x="Quarters",
            y=["MLE", "HE", "LE"],
            title=f"Quarterly Estimates {self.fy} <br><sup>{self.capital_project}, {self.fund.fund}</sup>",
            height=300,
            barmode="group",
        )
