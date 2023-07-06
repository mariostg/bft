from lineitems.models import LineItem, LineForecast
from costcenter.models import CostCenter, CostCenterAllocation, FundCenter
from django.db.models import Sum
import pandas as pd
from bft.exceptions import LineItemsDoNotExistError


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
            return None

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
        data = list(CostCenterAllocation.objects.all().values("costcenter__costcenter", "fund__fund", "amount", "fy"))
        columns = {
            "amount": "Allocation",
            "fy": "FY",
            "quarter": "Quarter",
            "costcenter__costcenter": "Cost Center",
            "fund__fund": "Fund",
        }
        df = pd.DataFrame(data).rename(columns=columns)
        return df

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

        with_allocation = False

        li_df = self.line_item_detailed()
        if len(li_df) == 0:
            return None
        grouping = ["Fund Center", "Cost Center", "Cost Center Name", "fund"]
        aggregation = {
            "Spent": "sum",
            "Balance": "sum",
            "Working Plan": "sum",
            "Forecast": "sum",
        }
        df = li_df.groupby(grouping).agg(aggregation)

        if with_allocation == True:
            allocation_df = self.cost_center_allocation_dataframe()
            allocation_agg = allocation_df.groupby(["Cost Center", "Fund"]).agg({"Allocation": "sum"})
            final = pd.merge(df, allocation_agg, how="left", on=["Cost Center"]).style.format("${0:>,.0f}")
            return final
        else:
            return df.style.format("${0:>,.0f}")

    def financial_structure_report(self):
        fc = self.fund_center_dataframe()
        cc = self.cost_center_dataframe()
        merged = pd.merge(fc, cc, how="left", left_on=["fundcenter_id"], right_on=["parent_id"])
        merged.set_index(
            ["Sequence No", "Fund Center Name", "Fund Center", "Cost Center Name", "Cost Center"], inplace=True
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

        def indent(s):
            return f"text-align:left;padding-left:{len(str(s))*4}px"

        merged = merged.style.applymap_index(indent, level=0).set_table_attributes("class=fin-structure")

        return merged.to_html(bold_rows=False)
        # return self.df_to_html(merged)
