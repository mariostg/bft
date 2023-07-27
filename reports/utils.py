from lineitems.models import LineItem, LineForecast
from costcenter.models import CostCenter, CostCenterAllocation, FundCenter, ForecastAdjustment
import pandas as pd
from pandas.io.formats.style import Styler
import numpy as np


class Report:
    def line_item_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the DRMIS line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of DRMIS line items
        """
        data = list(LineItem.objects.all().values())
        if data:
            df = pd.DataFrame(data).rename(
                columns={
                    "id": "lineitem_id",
                    "balance": "Balance",
                    "workingplan": "Working Plan",
                    "fundcenter": "Fund Center",
                    "spent": "Spent",
                }
            )
            return df
        else:
            return pd.DataFrame({})

    def forecast_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the forecast line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of forecast lines
        """
        data = list(LineForecast.objects.all().values())
        df = pd.DataFrame(data).rename(
            columns={
                "forecastamount": "Forecast",
            }
        )
        return df

    def fund_center_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the fund centers as per financial structure.
        Columns are renamed with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of fund centers.
        """

        data = list(FundCenter.objects.all().values())
        df = pd.DataFrame(data).rename(
            columns={
                "id": "fundcenter_id",
                "fundcenter": "Fund Center",
                "shortname": "Fund Center Name",
                "parent": "Parent",
                "sequence": "Sequence No",
            }
        )
        df["parent_id"] = df["parent_id"].fillna(0).astype("int")
        return df

    def cost_center_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the cost centers as per financial structure.
        Columns are renamed with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of cost centers.
        """
        data = list(CostCenter.objects.all().values())
        df = pd.DataFrame(data).rename(
            columns={
                "id": "costcenter_id",
                "costcenter": "Cost Center",
                "shortname": "Cost Center Name",
            }
        )
        return df

    def line_item_detailed(self) -> pd.DataFrame:
        """
        Prepare a pandas dataframe of merged line items, forecast line items and cost center.

        Returns:
            pd.DataFrame : A dataframe of line items including forecast.
        """
        li_df = self.line_item_dataframe()
        if li_df.empty:
            return li_df
        if len(li_df) > 0:
            fcst_df = self.forecast_dataframe()
            cc_df = self.cost_center_dataframe()

            if len(fcst_df) > 0:
                li_df = pd.merge(li_df, fcst_df, how="left", on="lineitem_id")
            else:
                li_df["Forecast"] = 0
            li_df = pd.merge(li_df, cc_df, how="left", on="costcenter_id")

        return li_df

    def cost_center_allocation_dataframe(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the cost center allocations for the given FY and Quarter.
        Columns are renamed with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of cost center allocations.
        """
        data = list(
            CostCenterAllocation.objects.all().values(
                "costcenter__parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
                "fy",
            )
        )
        columns = {
            "amount": "Allocation",
            "fy": "FY",
            "quarter": "Quarter",
            "costcenter__costcenter": "Cost Center",
            "costcenter__parent__fundcenter": "Fund Center",
            "fund__fund": "Fund",
        }
        df = pd.DataFrame(data).rename(columns=columns)
        return df

    def forecast_adjustment_dataframe(self) -> pd.DataFrame:
        data = list(
            ForecastAdjustment.objects.all().values(
                "costcenter__parent__fundcenter",
                "costcenter__costcenter",
                "fund__fund",
                "amount",
            )
        )
        columns = {
            "amount": "Forecast Adjustment",
            "costcenter__parent__fundcenter": "Fund Center",
            "costcenter__costcenter": "Cost Center",
            "fund__fund": "Fund",
        }
        return pd.DataFrame(data).rename(columns=columns)

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
        with_allocation = True
        with_forecast_adjustment = True
        li_df = self.line_item_detailed()
        li_df = li_df.rename(columns={"fund": "Fund"})
        if len(li_df) > 0:
            grouping = ["Fund Center", "Cost Center", "Fund"]
            aggregation = ["Spent", "Balance", "Working Plan", "Forecast"]
            df = pd.pivot_table(li_df, values=aggregation, index=grouping, aggfunc="sum")
            column_grouping = ["Fund Center", "Cost Center", "Fund"]
            if with_allocation == True:
                allocation_df = self.cost_center_allocation_dataframe()
                if not allocation_df.empty:
                    allocation_agg = pd.pivot_table(
                        allocation_df, values="Allocation", index=column_grouping, aggfunc=np.sum
                    )
                    df = pd.merge(df, allocation_agg, how="left", on=["Fund Center", "Cost Center", "Fund"])
            if with_forecast_adjustment == True:
                fa = self.forecast_adjustment_dataframe()
                if not fa.empty:
                    fa_agg = pd.pivot_table(fa, values="Forecast Adjustment", index=column_grouping, aggfunc=np.sum)
                    df = pd.merge(df, fa_agg, how="left", on=["Fund Center", "Cost Center", "Fund"]).fillna(0)
                    df["Forecast Total"] = df["Forecast"] + df["Forecast Adjustment"]
        return df

    def styler_clean_table(self, data: pd.DataFrame):
        """Clean up dataframe by stripping tag ids and format numbers."""
        return Styler(data, uuid_len=0, cell_ids=False).format("${0:>,.0f}")

    def financial_structure_data(self) -> pd.DataFrame | None:
        fc = self.fund_center_dataframe()
        cc = self.cost_center_dataframe()
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
            for column in grouper[n:]:
                table[column] = ""
            tables.append(table)
        concattable = pd.concat(tables).sort_index()
        concattable = concattable.set_index(keys=grouper)
        return concattable.sort_index(axis=0, ascending=True)
