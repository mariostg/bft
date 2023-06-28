from lineitems.models import LineItem, LineForecast
from costcenter.models import CostCenter, CostCenterAllocation
from django.db.models import Sum
import pandas as pd


class Report:
    def line_items(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the DRMIS line items.  Columns are renamed
        with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of DRMIS line items
        """
        data = list(LineItem.objects.all().all().values())
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

    def forecast(self) -> pd.DataFrame:
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

    def cost_center(self) -> pd.DataFrame:
        """Prepare a pandas dataframe of the cost centers as per financial structure.
        Columns are renamed with a more friendly name.

        Returns:
            pd.DataFrame: A dataframe of cost center
        """
        data = list(CostCenter.objects.all().values())
        df = pd.DataFrame(data).rename(
            columns={
                "id": "costcenter_id",
                "costcenter": "Cost Center",
            }
        )
        return df

    def cost_center_allocation(self) -> pd.DataFrame:
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

    def df_to_html(self, df: pd.DataFrame) -> str:
        """Create an html version of the dataframe provided.

        Args:
            df (pd.DataFrame): A dataframe to render as html

        Returns:
            str: HTML string of a dataframe.
        """
        report = df.to_html()
        return report

    def cost_center_screening_report(self) -> pd.DataFrame:
        """Create a dataframe of merged line items, forecast and cost centers grouped as per <grouping>.
        Aggregation is done on fields Spent, Balance, Working Plan, Forecast and Allocation

        Returns:
            pd.DataFrame: _description_
        """

        with_allocation = False

        r = Report()
        li_df = r.line_items()
        fcst_df = r.forecast()
        cc_df = r.cost_center()

        lifcst_df = pd.merge(li_df, fcst_df, how="left", on="lineitem_id")
        report = pd.merge(lifcst_df, cc_df, how="left", on="costcenter_id")
        grouping = ["Fund Center", "Cost Center", "fund"]
        aggregation = {
            "Spent": "sum",
            "Balance": "sum",
            "Working Plan": "sum",
            "Forecast": "sum",
        }
        df = report.groupby(grouping).agg(aggregation)

        if with_allocation == True:
            allocation_df = r.cost_center_allocation()
            allocation_agg = allocation_df.groupby(["Cost Center", "Fund"]).agg({"Allocation": "sum"})
            final = pd.merge(df, allocation_agg, how="left", on=["Cost Center"]).style.format("${0:>,.0f}")
            return final
        else:
            return df.style.format("${0:>,.0f}")
