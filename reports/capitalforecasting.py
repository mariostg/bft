from django.db.models import Sum, Value
from costcenter.models import (
    CapitalInYear,
    CapitalProject,
    CapitalYearEnd,
    CapitalNewYear,
    FundCenterManager,
    FundManager,
)
from bft.models import BftStatusManager
import pandas as pd
from reports.plotter import Plotter


class CapitalReport:
    def __init__(self, fund: str, capital_project: str, fy: int):
        self._dataset = None
        self.df = pd.DataFrame()
        self.quarters = [1, 2, 3, 4]
        if not fy:
            self.fy = BftStatusManager().fy()
        else:
            self.fy = fy
        self.capital_project = CapitalProject.objects.get(project_no=capital_project.upper())

        self.fund = FundManager().fund(fund)
        self.chart_width = 400
        self.layout_margin = dict(l=20, r=20, t=70, b=20)
        self.paper_bgcolor = "LightSteelBlue"
        self.plotter = Plotter()


class HistoricalOutlookReport(CapitalReport):
    """This class handles forecasts, spent, initial allocation on annual basis."""

    def __init__(self, fund: str, fy: int, capital_project: str):
        super().__init__(fund, capital_project, fy)
        self.years = list(range(self.fy - 4, self.fy + 1))

    def dataset(self):
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

    def dataframe(self):
        """Create a dataframe of annual data, one row per year for given fundcenter, project and fund"""

        data = self.dataset()
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

        df_year_end = pd.DataFrame.from_dict(data["year_end"])
        df = df.merge(df_year_end, how="left", on="fy")

        df_new_year = pd.DataFrame.from_dict(data["new_year"])
        self.df = df.merge(df_new_year, how="left", on="fy")
        self.df.rename(
            columns={"ye_spent": "YE Spent", "initial_allocation": "Initial Allocation"}, inplace=True
        )
        print(self.df)

    def to_html(self):
        self.dataframe()
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["Initial Allocation", "Q1 MLE", "Q2 MLE", "Q3 MLE", "Q4 MLE", "YE Spent"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )

    def chart(self):
        fig = self.plotter.bar_chart(
            self.df,
            x="fy",
            y=["Initial Allocation", "Q1 MLE", "Q2 MLE", "Q3 MLE", "Q4 MLE", "YE Spent"],
            fig_title=f"Historical Outlook - {self.capital_project}, {self.fund.fund}",
        )
        return fig

    def chart_ye_ratios(self):
        print("GGGGGGGG")
        try:
            self.df["YE vs Initial Allocation"] = self.df["YE Spent"] / self.df["Initial Allocation"]
            print(self.df)
        except:
            self.df["Initial Allocation"] = 0
            print("@@@@@Initial allocation")
        try:
            self.df["YE vs Q1"] = self.df["YE Spent"] / self.df["Q1 MLE"]
        except:
            self.df["Q1 MLE"] = 0
            print("@@@@@ Q1 MLE")
        try:
            self.df["YE vs Q2"] = self.df["YE Spent"] / self.df["Q2 MLE"]
        except:
            self.df["Q2 MLE"] = 0
            print("@@@@@ Q2 MLE")
        try:
            self.df["YE vs Q3"] = self.df["YE Spent"] / self.df["Q3 MLE"]
            print("@@@@@ Q3 MLE")
        except:
            self.df["Q3 MLE"] = 0
        print(self.df)
        fig = self.plotter.bar_chart(
            self.df,
            "fy",
            ["YE vs Initial Allocation", "YE vs Q1", "YE vs Q2", "YE vs Q3"],
            "Annual YE Spent Ratios",
            hline=1,
            hline_annotation="100%",
        )
        return fig


class FEARStatusReport(CapitalReport):
    """This class handles all quarter related fields"""

    def __init__(self, fund: str, fy: int = None, capital_project: str = None):
        self.quarters = [1, 2, 3, 4]
        super().__init__(fund, capital_project, fy)

    def dataset(self):
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

    def dataframe(self):
        """Create a dataframe of quarterly data, one row per quarter for given fundcenter, fund, and FY"""
        self.df = pd.DataFrame.from_dict(self.dataset())
        self.df.rename(columns={"quarter": "Quarters"}, inplace=True)

    def to_html(self):
        self.dataframe()
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["allocation", "forecast", "le", "he", "forecast", "co", "pc", "fr"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )

    def chart_bullet(self):
        self.dataframe()
        plotter = Plotter()
        # # FEAR Chart
        fig = plotter.bullet_chart(
            self.df.reset_index(),
            fig_title="FEAR Status (Forecast Encumbrance Allocation Relationship)",
            x_values=["Spent", "CO", "PC", "FR"],
            y="Quarters",
            piston="MLE",
            piston_name="Forecast",
            diamond="allocation",
            diamond_name="Allocation",
        )
        return fig


class EstimateReport(CapitalReport):
    """This class handles the LE, MLE, and HE of for the Capital Forecasting."""

    def __init__(self, fund: str, fy: int = None, capital_project: str = None):
        self.mle = self.he = self.le = []

        super().__init__(fund, capital_project, fy)

    def dataset(self):
        return (
            CapitalInYear.objects.filter(fy=self.fy, fund=self.fund)
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

    def dataframe(self):
        self.df = pd.DataFrame.from_dict(self.dataset())

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

    def chart(self):
        if self.df.empty:
            return "No figure."
        plotter = Plotter()
        fig = plotter.bar_chart(
            df=self.df,
            x="quarter",
            y=["LE", "MLE", "HE"],
            fig_title=f"Quarterly Estimates - {self.fy}{self.capital_project}, {self.fund.fund}",
            hline=self.df.working_plan[0],
            hline_annotation="Working Plan",
        )
        return fig
