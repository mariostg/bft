from lineitems.models import LineItem, LineForecast
from costcenter.models import CostCenter, CostCenterAllocation
from django.db.models import Sum
import pandas as pd


def prep_report():
    li = list(LineItem.objects.all().all().values())
    li_df = pd.DataFrame(li).rename(columns={"id": "lineitem_id"})

    fcst = list(LineForecast.objects.all().values())
    fcst_df = pd.DataFrame(fcst)

    lifcst_df = pd.merge(li_df, fcst_df, how="left", on="lineitem_id")

    cc = list(CostCenter.objects.all().values())
    cc_df = pd.DataFrame(cc).rename(columns={"id": "costcenter_id"})
    report = pd.merge(lifcst_df, cc_df, how="left", on="costcenter_id")

    grouping = report.groupby(["fundcenter", "costcenter", "fund"]).agg(
        {"spent": "sum", "workingplan": "sum", "forecastamount": "sum"}
    )

    print(grouping)
