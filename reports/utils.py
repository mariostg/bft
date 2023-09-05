from django.db.models import Sum, Value, Q, QuerySet, F
from bft.conf import P2Q
from bft import conf
from lineitems.models import LineItem
from costcenter.models import (
    CostCenter,
    CostCenterManager,
    CostCenterAllocation,
    FundCenter,
    FundCenterManager,
    FundManager,
    ForecastAdjustment,
    FinancialStructureManager,
)
from reports.models import CostCenterMonthly
from utils.dataframe import BFTDataFrame
import pandas as pd
from pandas.io.formats.style import Styler
import numpy as np


class Report:
    def df_to_html(self, df: pd.DataFrame, classname=None) -> str:
        """Create an html version of the dataframe provided.

        Args:
            df (pd.DataFrame): A dataframe to render as html

        Returns:
            str: HTML string of a dataframe.
        """
        if classname:
            report = df.style.set_table_attributes(f'class="{classname}"').to_html()
        else:
            report = df.to_html()
        return report

    def styler_clean_table(self, data: pd.DataFrame):
        """Clean up dataframe by stripping tag ids and format numbers."""
        return Styler(data, uuid_len=0, cell_ids=False).format("${0:>,.0f}")


class CostCenterMonthlyReport:
    def __init__(self, fy, period):
        fy = str(fy)
        period = str(period)
        self.fy = fy
        if conf.is_period(period):
            self.period = period
        else:
            raise ValueError(
                f"{period} is not a valid period.  Expected value is one of {(', ').join(map(str,conf.PERIODKEYS))}"
            )

    def sum_line_items(self) -> QuerySet:
        line_item_group = LineItem.objects.values("costcenter__costcenter", "fund").annotate(
            spent=Sum("spent"),
            commitment=Sum("balance", filter=Q(doctype="CO")),
            pre_commitment=Sum("balance", filter=Q(doctype="PC")),
            fund_reservation=Sum("balance", filter=Q(doctype="FR")),
            balance=Sum("balance"),
            working_plan=Sum("workingplan"),
            fy=Value(self.fy),
            period=Value(self.period),
            source=Value(""),
            costcenter=F("costcenter__costcenter"),
        )
        return line_item_group.values(
            "spent",
            "fund",
            "commitment",
            "pre_commitment",
            "fund_reservation",
            "balance",
            "working_plan",
            "fy",
            "period",
            "source",
            "costcenter",
        )

    def insert_line_items(self, lines: QuerySet) -> int:
        if len(lines) == 0:
            print("THERE ARE NO LINES")
            return 0
        CostCenterMonthly.objects.filter(fy=self.fy, period=self.period).delete()
        md = CostCenterMonthly.objects.bulk_create([CostCenterMonthly(**q) for q in lines])
        return len(md)

    def dataframe(self) -> pd.DataFrame:
        """Create a pandas dataframe using CostCenterMonthly data as source for the given FY and period.

        Returns:
            pandas.DataFrame: dataframe containing cost center monthly data with the following columns :
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Period",
            "Spent",
            "Commitment",
            "Pre Commitment",
            "Fund Reservation",
            "Balance",
            "Working Plan",
            "Allocation"
        """
        monthly_df = BFTDataFrame(CostCenterMonthly)
        monthly_df = monthly_df.build(CostCenterMonthly.objects.filter(fy=self.fy, period=self.period))

        alloc_df = CostCenterManager().allocation_dataframe(fy=self.fy, quarter=P2Q[self.period])
        alloc_df.drop(["FY", "Quarter"], axis=1, inplace=True)
        alloc_df["Allocation"].fillna(0, inplace=True)
        if not alloc_df.empty:
            monthly_df = pd.merge(monthly_df, alloc_df, how="left", on=["Cost Center", "Fund"])
        else:
            monthly_df["Allocation"] = 0
        monthly_df["Allocation"].fillna(0, inplace=True)
        monthly_df["Fund Center"].fillna("", inplace=True)
        columns = [
            "ID",
            "Fund",
            "Source",
            "Cost Center",
            "Fund Center",
            "FY",
            "Period",
            "Spent",
            "Commitment",
            "Pre Commitment",
            "Fund Reservation",
            "Balance",
            "Working Plan",
            "Allocation",
        ]
        return monthly_df[columns]


class CostCenterScreeningReport(Report):
    def __init__(self):
        self.column_grouping = [
            "Fund Center",
            "Cost Center",
            "Fund",
        ]
        self.aggregation_columns = [
            "Spent",
            "Balance",
            "Working Plan",
            "CO",
            "PC",
            "FR",
            "Forecast",
        ]
        self.with_allocation = False
        self.with_forecast_adjustment = False
        if CostCenterAllocation.objects.exists():
            self.with_allocation = True
        if ForecastAdjustment.objects.exists():
            # self.aggregation_columns.append("Forecast Adjustment")
            # self.aggregation_columns.append("Forecast Total")
            self.with_forecast_adjustment = True

    def cost_center_screening_report(self) -> pd.DataFrame:
        """Create a dataframe of merged line items, forecast and cost centers grouped as per <grouping>.
        Aggregation is done on fields Spent, Balance, Working Plan, Forecast and Allocation

        Returns:
            pd.DataFrame: _description_
        """
        df = pd.DataFrame()
        li_df = LineItem.objects.line_item_detailed()
        li_df = li_df.rename(columns={"fund": "Fund"})
        if len(li_df) > 0:
            df = pd.pivot_table(li_df, values=self.aggregation_columns, index=self.column_grouping, aggfunc="sum")
            if self.with_allocation == True:
                allocation_df = CostCenter.objects.allocation_dataframe()
                if not allocation_df.empty:
                    self.aggregation_columns.append("Allocation")
                    allocation_agg = pd.pivot_table(
                        allocation_df, values="Allocation", index=self.column_grouping, aggfunc=np.sum
                    )
                    df = pd.merge(df, allocation_agg, how="left", on=self.column_grouping)
            if self.with_forecast_adjustment == True:
                fa = CostCenter.objects.forecast_adjustment_dataframe()
                if not fa.empty:
                    self.aggregation_columns.append("Forecast Adjustment")
                    self.aggregation_columns.append("Forecast Total")
                    fa_agg = pd.pivot_table(
                        fa, values="Forecast Adjustment", index=self.column_grouping, aggfunc=np.sum
                    )
                    df = pd.merge(df, fa_agg, how="left", on=self.column_grouping).fillna(0)
                    df["Forecast Total"] = df["Forecast"] + df["Forecast Adjustment"]
        return df

    def financial_structure_dataframe(self) -> pd.DataFrame | None:
        fc = FundCenterManager().fund_center_dataframe(FundCenter.objects.all())
        cc = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())
        if fc.empty or cc.empty:
            return None
        merged = pd.merge(fc, cc, how="left", left_on=["Fund Center ID"], right_on=["parent_id"])
        print(merged)
        merged = merged.fillna("")
        # merged.set_index(["Sequence No", "Fund Center", "Cost Center", "Cost Center Name"], inplace=True)
        merged.set_index(["Fund Center", "Cost Center"], inplace=True)
        merged.drop(
            [
                "Fund Center ID",
                "parent_id_x",
                "Cost Center ID",
                "fund_id",
                "source_id",
                "parent_id_y",
            ],
            axis=1,
            inplace=True,
        )
        # merged.sort_values(by=["Sequence No"], inplace=True)

        return merged

    def financial_structure_styler(self, data: pd.DataFrame):
        def indent(s):
            return f"text-align:left;padding-left:{len(str(s))*4}px"

        def set_row_class(r):
            # TODO something to implement zebra rows in table
            pass

        html = Styler(data, uuid_len=0, cell_ids=False)
        table_style = [
            {"selector": "tbody:nth-child(odd)", "props": "background-color:red"},
        ]
        data = (
            html.applymap_index(indent, level=0)
            .set_table_attributes("class=fin-structure")
            .set_table_styles(table_style)
        )
        return data

    def pivot_table_w_subtotals(self, df: pd.DataFrame, aggvalues: list, grouper: list) -> pd.DataFrame:
        """
        Adds tabulated subtotals to pandas pivot tables with multiple hierarchical indices.

        Args:
        - df - dataframe used in pivot table
        - aggvalues - list-like or scalar to aggregate
        - grouper - ordered list of indices to aggregrate by
        - fill_value - value used to in place of empty cells

        Returns:
        -flat table with data aggregrated and tabulated

        """
        tables = []
        for indexnumber in range(len(grouper)):
            n = indexnumber + 1
            table = pd.pivot_table(
                df,
                values=aggvalues,
                index=grouper[:n],
                aggfunc=np.sum,
                fill_value="",
            ).reset_index()
            table = table.reindex(list(table.columns[:n]) + aggvalues, axis=1)
            for column in grouper[n:]:
                table[column] = ""
            tables.append(table)
        concattable = pd.concat(tables).sort_index()
        concattable = concattable.set_index(keys=grouper)
        return concattable.sort_index(axis=0, ascending=True)


class AllocationReport(Report):
    fsm = FinancialStructureManager()
    fcm = FundCenterManager()
    family_list = []
    df_main = None

    def _get_family_list(self, fc):
        """Recursive function to build a dataframe of descendants of specified fund center.

        Args:
        fc (FundCenter): Fund center object to get all descendants
        """
        while True:
            ct = self.fsm.has_children(fc)
            if ct:
                children = FundCenterManager().get_direct_descendants_dataframe(fc)
                self.family_list.append(children)
                if "fundcenter" in children:
                    for fc in children["fundcenter"]:
                        if type(fc) == str:
                            self._get_family_list(fc)
                break
            else:
                return

    def family_dataframe(
        self,
        root_fundcenter: str = None,
        fund: str = None,
    ) -> pd.DataFrame:
        if root_fundcenter:
            root_fundcenter = root_fundcenter.upper()
        root = FundCenter.objects.filter(fundcenter=root_fundcenter)
        fund = FundManager().fund(fund=fund)
        self.family_list = [pd.DataFrame(list(root.values()))]
        self._get_family_list(root.first())
        df_main = pd.concat(self.family_list).sort_values("sequence").fillna("")
        df_main["Cost Element"] = df_main.fundcenter + df_main.get("costcenter")
        df_main.drop(
            ["isforecastable", "isupdatable", "note", "source_id", "fund_id", "parent_id"],
            axis=1,
            inplace=True,
        )
        df_main.rename(columns={"fundcenter": "Fund Center", "costcenter": "Cost Center"}, inplace=True)

        return df_main

    def fc_allocation_dataframe(self, df_main: pd.DataFrame, fund, fy, quarter) -> pd.DataFrame:
        fc = list(filter(None, df_main["Fund Center"].to_list()))
        alloc_fc = []
        df_alloc_fc = pd.DataFrame()
        for f in fc:
            a = FundCenterManager().allocation_dataframe(f, fund, fy, quarter)
            if not a.empty:
                alloc_fc.append(a)
        if len(alloc_fc) > 0:
            df_alloc_fc = pd.concat(alloc_fc)
            df_alloc_fc["Cost Element"] = df_alloc_fc["Fund Center"]
            df_alloc_fc["Cost Center"] = ""
        return df_alloc_fc

    def cc_allocation_dataframe(self, df_main: pd.DataFrame, fund, fy, quarter) -> pd.DataFrame:
        cc = list(filter(None, df_main["Cost Center"].to_list()))
        alloc_cc = []
        df_alloc_cc = pd.DataFrame()
        for f in cc:
            a = CostCenterManager().allocation_dataframe(f, fund, fy, quarter)
            if not a.empty:
                alloc_cc.append(a)
        if len(alloc_cc) > 0:
            df_alloc_cc = pd.concat(alloc_cc)
            df_alloc_cc["Cost Element"] = df_alloc_cc["Cost Center"]
        return df_alloc_cc

    def allocation_status_dataframe(
        self,
        root_fundcenter: str = None,
        fund: str = None,
        fy: int = None,
        quarter: int = None,
    ) -> pd.DataFrame:

        df_main = self.family_dataframe(root_fundcenter, fund)

        # FC Allocations
        df_alloc_fc = self.fc_allocation_dataframe(df_main, fund, fy, quarter)

        # CC Allocations
        df_alloc_cc = self.cc_allocation_dataframe(df_main, fund, fy, quarter)

        # merge FC and CC allocation
        df_alloc = pd.concat([df_alloc_cc, df_alloc_fc])
        if df_alloc.empty:
            return pd.DataFrame()

        # Merge df_main with df_alloc and rearrange
        df_main.drop(["Cost Center", "Fund Center"], inplace=True, axis=1)
        df_main = pd.merge(
            df_main,
            df_alloc,
            how="inner",
            on=["Cost Element"],
        )
        df_main.sort_values("sequence", inplace=True)
        df_main = df_main[
            [
                "sequence",
                "Fund Center",
                "Cost Center",
                "shortname",
                "Fund",
                "Allocation",
                "FY",
                "Quarter",
                "Cost Element",
            ]
        ]
        df_main.fillna("", inplace=True)
        df_main.set_index(["sequence", "Fund Center", "Cost Center", "Fund"], inplace=True)

        return df_main
