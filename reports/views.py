from django.core.paginator import Paginator
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
import csv

from lineitems.models import LineItem
from reports import utils, screeningreport

from costcenter.models import (
    CostCenterAllocation,
    FundManager,
    FundCenterAllocation,
    FundCenterManager,
    FinancialStructureManager,
    ForecastAdjustmentManager,
    CapitalForecasting,
)
from charges.models import CostCenterChargeMonthly
from reports.forms import SearchAllocationAnalysisForm, SearchCostCenterScreeningReportForm
from bft.models import BftStatus
from bft.conf import QUARTERKEYS
from bft.exceptions import LineItemsDoNotExistError
from utils.getrequestfilter import set_query_string


def _orphan_forecast_adjustments(request, allocations, forecast_adjustment):
    # for fcst_adj_path, fcst_adj_item in forecast_adjustment.items():
    alloc_paths = allocations.keys()
    for fcst_path, fcst_item in forecast_adjustment.items():
        if fcst_path not in alloc_paths:
            messages.warning(
                request, f"Cost center {fcst_item['Cost Element']} has forecast adjustment but no allocation"
            )


def bmt_screening_report(request):
    fundcenter = fund = ""
    fy = BftStatus.current.fy()
    quarter = BftStatus.current.quarter()
    query_string = None
    table = None
    form_filter = True
    context = {}

    has_cc_allocation = CostCenterAllocation.objects.exists()
    has_fc_allocation = FundCenterAllocation.objects.exists()

    if not len(request.GET) and not has_cc_allocation and not has_fc_allocation:
        messages.warning(request, "There are no allocation to report, hence nothing really to screen")
        form_filter = False

    if len(request.GET):
        fundcenter = FundCenterManager().get_request(request)
        fund = FundManager().get_request(request)
        quarter = int(request.GET.get("quarter")) if request.GET.get("quarter") else 0
        fy = int(request.GET.get("fy")) if request.GET.get("fy") else 0

        if str(quarter) not in QUARTERKEYS:
            messages.warning(request, "Quarter is invalid.  Either value is missing or outside range")
        if fundcenter and fund and quarter and fy:
            query_string = set_query_string(fundcenter=fundcenter, fund=fund, fy=fy, quarter=quarter)

    initial = {
        "fundcenter": fundcenter,
        "fund": fund,
        "fy": fy,
        "quarter": quarter,
    }

    if query_string and (has_cc_allocation or has_fc_allocation):
        fund = FundManager().fund(fund)
        fundcenter = FundCenterManager().fundcenter(fundcenter)
    if fundcenter and fund:
        sr = screeningreport.ScreeningReport(fundcenter, fund, fy, quarter)
        try:
            sr.main()
            table = sr.html()
        except LineItemsDoNotExistError:
            messages.warning(request, f"No lines items found for {fund} and {fundcenter}")
            table = ""

    form = SearchCostCenterScreeningReportForm(initial=initial)
    context = {
        "form": form,
        "form_filter": form_filter,
        "initial": initial,
        "table": table,
        "fy": BftStatus.current.fy(),
    }
    return render(request, "bmt-screening-report.html", context)


def allocation_status_report(request):
    """This function relies on provision of fundcenter, fund, fy, quarter which are extracted from GET request.  If not
    part of GET request, exception will be raised and displayed as a message to the user.

    Args:
        request (HtpRequest): _description_

    Returns:
        Content to display the Allocation Status Report
    """

    fundcenter = fund = fy = quarter = ""
    context = {}  # Dict sent to the template
    table = None  # dataframe html formatted to include in context
    form_filter = True
    has_cc_allocation = CostCenterAllocation.objects.exists()
    has_fc_allocation = FundCenterAllocation.objects.exists()

    if not len(request.GET) and not has_cc_allocation and not has_fc_allocation:
        messages.warning(request, "There are no allocation to report")
        form_filter = False

    if len(request.GET):
        fundcenter = FundCenterManager().get_request(request)
        fund = FundManager().get_request(request)
        quarter = int(request.GET.get("quarter")) if request.GET.get("quarter") else 0
        fy = int(request.GET.get("fy")) if request.GET.get("fy") else 0

        if str(quarter) not in QUARTERKEYS:
            messages.warning(request, "Quarter is invalid.  Either value is missing or outside range")

    initial = {
        "fundcenter": fundcenter,
        "fund": fund,
        "fy": BftStatus.current.fy(),
        "quarter": BftStatus.current.quarter(),
    }

    if has_cc_allocation or has_fc_allocation:
        r = utils.AllocationStatusReport()
        table = r.main(
            fundcenter, fund, fy, quarter
        )  # allocation_status_dataframe(fundcenter, fund, fy, int(quarter))

    form = SearchAllocationAnalysisForm(initial=initial)
    context = {
        "form": form,
        "form_filter": form_filter,
        "table": table,
    }
    return render(request, "allocation-status-report.html", context)


def costcenter_monthly_data(request):
    s = BftStatus.current
    r = utils.CostCenterMonthlyReport(fy=s.fy(), period=s.period())
    df = r.dataframe()

    df = df.style.format(thousands=",")
    return render(request, "costcenter-monthly-data.html", {"table": df.to_html()})


def line_items(request):
    data = (
        LineItem.objects.annotate(doc=Concat("docno", V("-"), "lineno"))
        .order_by("fundcenter", "costcenter", "fund", "docno", "lineno")
        .filter(balance__gt=0)
    )
    paginator = Paginator(data, 25)
    page_number = request.GET.get("page")
    context = {"data": paginator.get_page(page_number)}
    return render(request, "lineitem-report.html", context)


def financial_structure_report(request):
    fsm = FinancialStructureManager()
    data = fsm.financial_structure_dataframe()
    if not data.empty:
        data = fsm.financial_structure_styler(data)
        data = data.to_html(bold_rows=False)
    else:
        messages.info(request, "No data")
        data = ""
    return render(request, "financial-structure-report.html", {"table": data})


"""
Writes line item report to csv.
"""


def csv_line_items(request):
    data = (
        LineItem.objects.annotate(doc=Concat("docno", V("-"), "lineno"))
        .order_by("fundcenter", "costcenter", "fund", "docno", "lineno")
        .filter(balance__gt=0)
    )
    field_names = [field.name for field in data.model._meta.fields]
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="lineitems.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(field_names)
    for obj in data:
        writer.writerow([getattr(obj, field) for field in field_names])
    return response


def cost_center_charge_table(request, cc: str, fy: int, period: int):
    cc = cc.upper()
    table = ""
    data = CostCenterChargeMonthly.objects.filter(costcenter=cc, fy=fy, period=period)
    if data:
        df = utils.BFTDataFrame(CostCenterChargeMonthly).build(data).set_index(["Cost Center", "Fund"])
        df = df[["Amount", "Fiscal Year", "Period"]]
        df = df.style.format(thousands=",")
        table = df.to_html()
    else:
        messages.info(request, f"There are no charges agains {cc} for FY {fy} and period {period}")
    return render(request, "costcenter-monthly-charge-data.html", {"table": table})


def capital_forecasting_table(request):
    data = CapitalForecasting.objects.all()
    df = utils.BFTDataFrame(CapitalForecasting).build(data)  # .set_index(["fundcenter", "fy", "fund"])
    print(df)
    table = df.to_html()
    return render(request, "capital-forecasting-table.html", {"table": table})
