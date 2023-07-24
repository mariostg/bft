"""
Just a file to experiment with code as needed
"""
import os, sys
from pathlib import Path

PWD = os.getenv("PWD")
BASE_DIR = Path(PWD).resolve()
print(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
import django

django.setup()

from reports.utils import Report
import pandas as pd
import numpy as np

pd.set_option("display.max_columns", 10)
pd.set_option("display.max_colwidth", 150)
pd.set_option("display.width", 200)
r = Report()


with_allocation = True
with_forecast_adjustment = True
li_df = r.line_item_detailed()
li_df = li_df.rename(columns={"fund": "Fund"})
if len(li_df) > 0:
    grouping = ["Fund Center", "Cost Center", "Fund"]
    aggregation = ["Spent", "Balance", "Working Plan", "Forecast"]
    df = pd.pivot_table(li_df, values=aggregation, index=grouping, aggfunc=np.sum)
    column_grouping = ["Fund Center", "Cost Center", "Fund"]
    if with_allocation == True:
        allocation_df = r.cost_center_allocation_dataframe()
        if not allocation_df.empty:
            allocation_agg = pd.pivot_table(allocation_df, values="Allocation", index=column_grouping, aggfunc=np.sum)
            df = pd.merge(df, allocation_agg, how="left", on=["Fund Center", "Cost Center", "Fund"])
    if with_forecast_adjustment == True:
        fa = r.forecast_adjustment_dataframe()
        if not fa.empty:
            fa_agg = pd.pivot_table(fa, values="Forecast Adjustment", index=column_grouping, aggfunc=np.sum)
            df = pd.merge(df, fa_agg, how="left", on=["Fund Center", "Cost Center", "Fund"]).fillna(0)
            df["Total Forecast"] = df["Forecast"] + df["Forecast Adjustment"]

    print(df)


def pivot_table_w_subtotals(df: pd.DataFrame, aggvalues: list, grouper: list) -> pd.DataFrame:
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
    listOfTable = []
    for indexNumber in range(len(grouper)):
        n = indexNumber + 1
        table = pd.pivot_table(
            df,
            values=aggvalues,
            index=grouper[:n],
            aggfunc=np.sum,
            fill_value="",
        ).reset_index()
        for column in grouper[n:]:
            table[column] = ""
        listOfTable.append(table)
    concatTable = pd.concat(listOfTable).sort_index()
    concatTable = concatTable.set_index(keys=grouper)
    return concatTable.sort_index(axis=0, ascending=True)


table = pivot_table_w_subtotals(
    df=df,
    aggvalues=["Spent", "Balance", "Working Plan", "Forecast", "Forecast Adjustment", "Total Forecast", "Allocation"],
    grouper=["Fund Center", "Cost Center", "Fund"],
)

print(table)
