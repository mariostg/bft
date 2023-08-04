from lineitems.models import LineItem, LineForecast
from costcenter.models import CostCenter, CostCenterAllocation, FundCenter, ForecastAdjustment
import pandas as pd
from pandas.io.formats.style import Styler
import numpy as np


class Report:
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

    def styler_clean_table(self, data: pd.DataFrame):
        """Clean up dataframe by stripping tag ids and format numbers."""
        return Styler(data, uuid_len=0, cell_ids=False).format("${0:>,.0f}")

    def financial_structure_data(self) -> pd.DataFrame | None:
        fc = FundCenter.objects.fund_center_dataframe()
        cc = CostCenter.objects.cost_center_dataframe()
        if fc.empty or cc.empty:
            return None
        merged = pd.merge(fc, cc, how="left", left_on=["fundcenter_id"], right_on=["parent_id"])
        merged = merged.fillna("")
        merged.set_index(
            ["Sequence No", "Fund Center Name", "Fund Center", "Cost Center", "Cost Center Name"], inplace=True
        )
        merged.drop(
            [
                "fundcenter_id",
                "parent_id_x",
                "costcenter_id",
                "fund_id",
                "source_id",
                "parent_id_y",
            ],
            axis=1,
            inplace=True,
        )
        merged.sort_values(by=["Sequence No"], inplace=True)

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
            table = table.reindex(list(table.columns[:n]) + self.aggregation_columns, axis=1)
            for column in grouper[n:]:
                table[column] = ""
            tables.append(table)
        concattable = pd.concat(tables).sort_index()
        concattable = concattable.set_index(keys=grouper)
        return concattable.sort_index(axis=0, ascending=True)
