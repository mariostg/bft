from django.db.models import Sum, Value, Q, QuerySet, F
from bft.conf import P2Q
from bft import conf
from lineitems.models import LineItem
from costcenter.models import (
    CostCenter,
    CostCenterManager,
    CostCenterAllocation,
    Fund,
    FundCenter,
    FundCenterAllocation,
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
        if monthly_df.empty:
            return pd.DataFrame()

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
        monthly_df = monthly_df.reindex(columns=columns).set_index(
            ["Fund Center", "Cost Center", "Fund", "Source", "FY", "Period"]
        )
        return monthly_df


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
            "Workingplan",
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
        li_df = LineItem.objects.line_item_detailed_dataframe()
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

    def financial_structure_dataframe(self) -> pd.DataFrame:
        fc = FundCenterManager().fund_center_dataframe(FundCenter.objects.all())
        cc = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())
        if fc.empty or cc.empty:
            return pd.DataFrame()
        merged = pd.merge(
            fc,
            cc,
            how="left",
            left_on=["Fundcenter_ID", "FC Path", "Fund Center", "Fund Center Name"],
            right_on=["Costcenter_parent_ID", "FC Path", "Fund Center", "Fund Center Name"],
        )
        print(merged)
        merged = merged.fillna("")
        merged.set_index(
            ["FC Path", "Fund Center", "Fund Center Name", "Cost Center", "Cost Center Name"], inplace=True
        )
        merged.drop(
            [
                "Fundcenter_ID_x",
                "Fundcenter_ID_y",
                "Fundcenter_parent_ID_x",
                "Fundcenter_parent_ID_y",
                "Costcenter_ID",
                "Fund_ID",
                "Source_ID",
                "Costcenter_parent_ID",
            ],
            axis=1,
            inplace=True,
        )
        merged.sort_values(by=["FC Path"], inplace=True)

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


class AllocationStatusReport:
    def fund_center_alloc_to_dict(self, alloc: QuerySet[FundCenterAllocation]) -> dict:
        if not alloc:
            return {}
        lst = {}
        try:
            iter(alloc)
        except TypeError:
            alloc = [alloc]
        for item in alloc:
            id = item.fundcenter.id
            fc = item.fundcenter
            pid = fc.fundcenter_parent.id
            d = {
                "Cost Element": fc.fundcenter,
                "Cost Element Name": fc.shortname,
                "Fund Center ID": fc.id,
                "Parent ID": pid,
                "Path": fc.sequence,
                "Parent Path": fc.fundcenter_parent.sequence,
                "Allocation": float(item.amount),
                "Type": "FC",
            }
            lst[id] = d
        return lst

    def fund_center_set_sub_id(self, alloc: dict) -> dict:
        d = {}
        for id in alloc:
            pid = alloc[id]["Parent ID"]
            if not d.get(id):
                d[id] = alloc.get(id)
                d[id]["sub_id"] = []
            if not d.get(pid):
                d[pid] = alloc.get(pid, {})
                d[pid]["sub_id"] = [id]
            else:
                d[pid]["sub_id"].append(id)
        return d

    def cost_center_alloc_to_dict(self, alloc: QuerySet[CostCenterAllocation]) -> dict:
        lst = {}
        d = {}
        for item in alloc:
            id = item.costcenter.id
            cc = item.costcenter
            pid = cc.costcenter_parent.id
            d = {
                "Cost Element": cc.costcenter,
                "Cost Element Name": cc.shortname,
                "Fund Center ID": cc.id,
                "Parent ID": pid,
                "Path": cc.sequence,
                "Parent Path": cc.costcenter_parent.sequence,
                "Allocation": float(item.amount),
                "Type": "CC",
            }
            lst[id] = d
        return lst

    def main(self, fundcenter: str, fund: str, fy: int, quarter: int) -> str:
        fcm = FundCenterManager()
        ccm = CostCenterManager()
        root = fcm.fundcenter(fundcenter)

        fc = FundCenter.objects.filter(sequence__startswith=root.sequence)
        fc_list = list(fc.values_list("fundcenter", flat=True))
        alloc_fc = fcm.allocation(fundcenter=fc_list, fund=fund, fy=fy, quarter=quarter)

        cc = CostCenter.objects.filter(sequence__startswith=root.sequence)
        cc_list = list(cc.values_list("costcenter", flat=True))
        alloc_cc = ccm.allocation(costcenter=cc_list, fund=fund, fy=fy, quarter=quarter)

        data_fc = self.fund_center_alloc_to_dict(alloc_fc)
        data_cc = self.cost_center_alloc_to_dict(alloc_cc)
        data = self.fund_center_set_sub_id({**data_fc, **data_cc})

        for v in data.values():
            ce = v.get("Cost Element")
            if not ce:
                continue

            tbody = ""
            zebra = {0: "fc-even", -1: "fc-odd"}
            odd = 0
            for allocation in data.values():
                ce = allocation.get("Cost Element")
                if not ce or allocation.get("Type") == "CC":
                    continue
                odd = ~odd

                trow = f"<tr class='{zebra[odd]}'>"
                trow += f"<td>{ce}</td>"
                parent_allocation = int(allocation.get("Allocation"))
                if parent_allocation:
                    trow += f"<td class='numbers'>{parent_allocation:,}</td>"
                    subtotal = variation = 0
                    sub_id = allocation.get("sub_id")
                    sub_table = ""
                    if sub_id:
                        sub_table = "<table>"
                        for sid in sub_id:
                            sub_row = "<tr>"
                            sub_data = data.get(sid)
                            sub_allocation = int(sub_data.get("Allocation", 0))
                            sub_ce = sub_data.get("Cost Element")
                            sub_row += f"<td>{sub_ce}</td><td class='numbers'> {sub_allocation:,}</td><tr>"
                            subtotal += sub_allocation
                            sub_table += sub_row

                        variation = parent_allocation - subtotal
                        if variation:
                            sub_table += f"<tr><td>Sub Total</td><td class='numbers'>{subtotal:,}</td></tr><tr><td class='alert--warning'>Variation</td><td class='numbers'>{variation:,}</td></tr>"
                        else:
                            sub_table += f"<tr><td>Sub Total</td><td class='numbers'>{subtotal:,}</td></tr>"
                        sub_table = f"<td>{sub_table}</td>"
                    else:
                        sub_table = "<td class='alert--info'>No Sub Allocation</td>"

                    trow += f"{sub_table}</table>"
                tbody += trow
                print("======")
                print(tbody)
            thead = "<thead><th>Fund Center</th><th>Allocation</th><th>Sub-Allocations</th></thead>"
            table = f"<table class=''>{thead}{tbody}</table>"
            return table
