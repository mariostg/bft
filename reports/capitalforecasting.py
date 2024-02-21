from django.db.models import Sum, Value
from costcenter.models import CapitalForecasting, CapitalProject, FundCenterManager, FundManager
from bft.models import BftStatusManager
import pandas as pd
from reports.plotter import Plotter


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
        self.chart_width = 400
        self.layout_margin = dict(l=20, r=20, t=70, b=20)
        self.paper_bgcolor = "LightSteelBlue"
        self.plotter = Plotter()


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
        self.df.rename(
            columns={
                "initial_allocation": "Initial Allocation",
                "q1_forecast": "Q1 Forecast",
                "q2_forecast": "Q2 Forecast",
                "q3_forecast": "Q3 Forecast",
                "ye_spent": "YE Spent",
            },
            inplace=True,
        )

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
        fig = self.plotter.bar_chart(
            self.df,
            x="fy",
            y=["Initial Allocation", "Q1 Forecast", "Q2 Forecast", "Q3 Forecast", "YE Spent"],
            fig_title=f"Historical Outlook - {self.capital_project}, {self.fund.fund}",
        )
        return fig

    def chart_ye_ratios(self):
        self.df["YE vs Initial Allocation"] = self.df["YE Spent"] / self.df["Initial Allocation"]
        self.df["YE vs Q1"] = self.df["YE Spent"] / self.df["Q1 Forecast"]
        self.df["YE vs Q2"] = self.df["YE Spent"] / self.df["Q2 Forecast"]
        self.df["YE vs Q3"] = self.df["YE Spent"] / self.df["Q3 Forecast"]

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
                Spent=Sum(f"q{quarter}_spent"),
                CO=Sum(f"q{quarter}_co"),
                PC=Sum(f"q{quarter}_pc"),
                FR=Sum(f"q{quarter}_fr"),
            )
        )

    def dataframe(self):
        """Create a dataframe of quarterly data, one row per quarter for given fundcenter, fund, and FY"""
        self.df = pd.DataFrame()
        for q in [1, 2, 3, 4]:
            df = pd.DataFrame.from_dict(self.dataset(q))
            df["Quarters"] = q
            self.df = pd.concat([self.df, df])
        self.df = self.df.set_index(["Quarters"])

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
            piston="forecast",
            piston_name="Forecast",
            diamond="allocation",
            diamond_name="Allocation",
            # v_line=1111,  # self.df.working_plan[0],
            # v_line_text="Working Plan",
        )
        return fig


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
                working_plan=Value(3000),
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
        self.working_plan = _dataset["working_plan"]

    def dataframe(self):
        self.dataset()
        self.quarterly()
        self.df = pd.DataFrame(
            {
                "Quarters": self.quarters,
                "LE": self.le,
                "MLE": self.mle,
                "HE": self.he,
                "working_plan": self.working_plan,
            }
        )

    def to_html(self):
        self.dataframe()
        fmt = "{:,.0f}".format
        fmt_dict = {}
        for field in ["MLE", "HE", "LE", "working_plan"]:
            fmt_dict[field] = fmt
        return self.df.to_html(
            formatters=fmt_dict,
        )

    def chart(self):
        plotter = Plotter()
        fig = plotter.bar_chart(
            df=self.df,
            x="Quarters",
            y=["LE", "MLE", "HE"],
            fig_title=f"Quarterly Estimates - {self.fy}{self.capital_project}, {self.fund.fund}",
            hline=self.df.working_plan[0],
            hline_annotation="Working Plan",
        )
        return fig
