import pandas as pd
from django.db.models.functions import Cast
from django.db.models import Q
from django.db.models import IntegerField
from django.db.models import Sum
from costcenter.models import (
    FundCenterManager,
    FundManager,
    Fund,
    FundCenter,
    CostCenter,
    CostCenterAllocation,
    FundCenterAllocation,
    ForecastAdjustment,
)
from lineitems.models import LineItem
from bft.exceptions import LineItemsDoNotExistError


def caster(value):
    return Cast(value, IntegerField())


class ScreeningReport:
    def __init__(self, top_fc: FundCenter, fund: Fund, fy: int, quarter: int):
        self.top_fc = top_fc
        self.fund = fund
        self.fy = fy
        self.quarter = quarter

        self.cc_children = CostCenter.objects.filter(sequence__startswith=self.top_fc.sequence)
        self.report_lines = None
        self.cc_allocations = None
        self.fc_allocations = None
        self.fcst_adj = pd.DataFrame
        self.allocations_without_encumbrance = pd.DataFrame  # Keep track for reporting purposes
        self.line_item_with_allocations = None
        self.report = pd.DataFrame
        self.grand_total = pd.DataFrame

    def get_lineitems_grouping(self) -> pd.DataFrame:
        """Get a grouped dataframe for all lines items summarizing wp, spent, balance, CO, PC, FR. Group by Cost Center and Fund."""
        line_fields = [
            "fundcenter",
            "fund",
            "costcenter__sequence",
            "costcenter__costcenter",
        ]

        lines = LineItem.objects.filter(costcenter__in=self.cc_children, fund=self.fund.fund)
        if len(lines) == 0:
            return pd.DataFrame
        lines = lines.values(*line_fields).annotate(
            Spent=caster(Sum("spent")),
            Balance=caster(Sum("balance")),
            Working_plan=caster(Sum("workingplan")),
            CO=caster(Sum("balance", filter=Q(doctype="CO"), default=0)),
            PC=caster(Sum("balance", filter=Q(doctype="PC"), default=0)),
            FR=caster(Sum("balance", filter=Q(doctype="FR"), default=0)),
            Forecast=caster(Sum("fcst__forecastamount", default=0)),
        )
        df = pd.DataFrame(lines)
        df = df.rename(columns={"costcenter__sequence": "sequence", "costcenter__costcenter": "costcenter"})
        grouped = df.groupby(["fundcenter", "costcenter", "fund", "sequence"]).sum()
        return grouped

    def get_cost_center_allocations(self) -> pd.DataFrame:
        """Get an allocation dataframe for all cost centers children of specified fund center."""
        allocation_fields = [
            "costcenter__sequence",
            "costcenter__costcenter",
            "amount",
            "costcenter__costcenter_parent__fundcenter",
            "fund__fund",
        ]
        costcenters = CostCenter.objects.filter(sequence__startswith=self.top_fc.sequence)
        allocations = CostCenterAllocation.objects.filter(
            costcenter__in=costcenters, fy=self.fy, quarter=self.quarter, fund=self.fund
        ).values(*allocation_fields)
        df = pd.DataFrame(allocations)
        df = df.rename(
            columns={
                "fund__fund": "fund",
                "costcenter__sequence": "sequence",
                "costcenter__costcenter": "costcenter",
                "amount": "Allocation",
                "costcenter__costcenter_parent__fundcenter": "fundcenter",
            }
        )
        if df.empty:
            return pd.DataFrame(
                {"Allocation": [0], "fundcenter": "", "costcenter": "", "fund": "", "sequence": ""}
            )
        return df

    def get_fundcenter_allocations(self) -> pd.DataFrame:
        """Get an allocation dataframe for all fundcenters un specified fund center including itself."""
        allocation_fields = [
            "fundcenter__sequence",
            "fundcenter__fundcenter",
            "amount",
            "fund__fund",
        ]
        fundcenters = FundCenter.objects.filter(sequence__startswith=self.top_fc.sequence)
        allocations = FundCenterAllocation.objects.filter(
            fundcenter__in=fundcenters, fy=self.fy, quarter=self.quarter, fund=self.fund
        ).values(*allocation_fields)
        df = pd.DataFrame(allocations)
        df = df.rename(
            columns={
                "fundcenter__sequence": "sequence",
                "fundcenter__fundcenter": "fundcenter",
                "amount": "Allocation",
                "fund__fund": "fund",
            }
        )
        return df

    def get_forecast_adjustments(self) -> pd.DataFrame:
        costcenters = CostCenter.objects.filter(sequence__startswith=self.top_fc.sequence)
        fcst_fields = [
            "costcenter__sequence",
            "costcenter__costcenter",
            "amount",
            "costcenter__costcenter_parent__fundcenter",
            "fund__fund",
        ]
        self.fcst_adj = ForecastAdjustment.objects.filter(costcenter__in=costcenters, fund=self.fund).values(
            *fcst_fields
        )
        df = pd.DataFrame(self.fcst_adj)
        df = df.rename(
            columns={
                "fund__fund": "fund",
                "costcenter__sequence": "sequence",
                "costcenter__costcenter": "costcenter",
                "amount": "fcst adj",
                "costcenter__costcenter_parent__fundcenter": "fundcenter",
            }
        )
        if df.empty:
            return pd.DataFrame(
                {"fcst adj": [0], "fundcenter": "", "costcenter": "", "fund": "", "sequence": ""}
            )
        return df

    def grand_total_by_fund(self, df: pd.DataFrame):
        grouping = df.groupby("fund").sum()
        return grouping

    def report_subtotals(self, df: pd.DataFrame) -> pd.DataFrame:
        report = df.reset_index()
        sequences = report["sequence"].items()
        for i, s in sequences:
            descendants = report[
                (report["sequence"].str.startswith(s)) & (report["fund"] == report["fund"][i])
            ]
            report.at[i, "Spent"] = descendants["Spent"].sum()
            report.at[i, "Balance"] = descendants["Balance"].sum()
            report.at[i, "Working_plan"] = descendants["Working_plan"].sum()
            report.at[i, "CO"] = descendants["CO"].sum()
            report.at[i, "PC"] = descendants["PC"].sum()
            report.at[i, "FR"] = descendants["FR"].sum()
            report.at[i, "Forecast"] = descendants["Forecast"].sum()
            report.at[i, "fcst adj"] = descendants["fcst adj"].sum()
            report.at[i, "Allocation_calc"] = descendants["Allocation"].sum() - report.at[i, "Allocation"]
        report = report.set_index(["sequence", "fundcenter", "costcenter", "fund"]).sort_index()
        return report

    def html(self):
        rows = self.report.reset_index()
        data_dict = {}
        tdrows = []
        th = []
        for c in rows.columns:
            data_dict[c] = (rows[c].to_numpy()).tolist()
            th.append(f"<th>{c}</th>")
        thead = f"<thead>{('').join(th)}</thead>"
        for i, v in enumerate(data_dict["sequence"]):
            td = ""
            for c in rows.columns:
                try:
                    val = f"{round(data_dict[c][i]):,}"
                except:
                    val = data_dict[c][i]
                td += f"<td>{val}</td>"
            level = len(v.split("."))
            tdrows.append(f"<tr class='level{level}'>{td}</tr>")
        return f"<table id='screeningreport'>{thead}{('').join(tdrows)}</table>"

    def main(self):
        self.report_lines = self.get_lineitems_grouping()
        if self.report_lines.empty:
            raise LineItemsDoNotExistError("No Line to report")
        self.cc_allocations = self.get_cost_center_allocations()
        self.fc_allocations = self.get_fundcenter_allocations()
        self.fcst_adj = self.get_forecast_adjustments()
        # merge allocations with encumbrance
        self.line_item_with_allocations = self.report_lines.merge(
            self.cc_allocations,
            how="left",
            on=["fundcenter", "costcenter", "fund", "sequence"],
        )

        # allocation without encumbrance
        awe = self.report_lines.merge(self.cc_allocations, how="right", on="sequence")
        self.allocations_without_encumbrance = awe[awe.Working_plan.isna()].fillna(0)

        # concat fund centers allocations
        report = pd.concat([self.line_item_with_allocations, self.fc_allocations])

        # merge Forecast adjustment
        report = report.merge(
            self.fcst_adj, how="left", on=["fundcenter", "costcenter", "fund", "sequence"], validate="1:1"
        )

        report = report.set_index(["sequence", "fundcenter", "costcenter", "fund"]).sort_index()
        self.report = self.report_subtotals(report)
        # Grand Total
        self.grand_total = self.grand_total_by_fund(self.report_lines)
