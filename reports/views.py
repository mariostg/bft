from django.core.paginator import Paginator
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
import csv

from lineitems.models import LineItem
from reports import utils

from costcenter.models import CostCenterAllocation, FundManager, FundCenterAllocation, FundCenterManager
from reports.forms import SearchAllocationAnalysisForm
from reports.models import CostCenterMonthly
from bft.models import BftStatus
from bft.conf import QUARTERKEYS


def bmt_screening_report(request):
    context = {}
    if LineItem.objects.exists():
        r = utils.CostCenterScreeningReport()
        table = r.cost_center_screening_report()
        table = r.pivot_table_w_subtotals(
            table,
            aggvalues=r.aggregation_columns,
            grouper=r.column_grouping,
        )
        table = r.styler_clean_table(table)
        context = {"table": table.to_html()}
    return render(request, "bmt-screening-report.html", context)


def allocation_status_report(request):
    """This function relies on provision of fundcenter, fund, fy, quarter which are extracted from GET request.  If not
    part of GET request, exception will be raised and displayed as a message to the user.

    Args:
        request (HtpRequest): _description_

    Returns:
        HttpResponse: Content to display the Allocation Status Report
    """

    fundcenter = fund = fy = quarter = ""
    query_string = None  # Keep query_string in case paginator is required when more data is used.
    context = {}  # Dict sent to the template
    table = None  # dataframe html formatted to include in context
    form_filter = True

    def set_query_string(fundcenter, fund, fy, quarter):
        query_terms = set()  # Concatenation will produce query string
        query_terms.add(f"fundcenter={fundcenter}")
        query_terms.add(f"fund={fund}")
        query_terms.add(f"quarter={quarter}")
        query_terms.add(f"fy={fy}")
        if len(query_terms) > 0:
            query_string = "&".join(query_terms)
        return query_string

    if not len(request.GET) and not CostCenterAllocation.objects.exists() and not FundCenterAllocation.objects.exists():
        messages.warning(request, "There are no allocation to report")
        form_filter = False

    if len(request.GET):
        try:
            fundcenter = FundCenterManager().get_request(request)
            fund = FundManager().get_request(request)
            quarter = int(request.GET.get("quarter")) if request.GET.get("quarter") else 0
            fy = int(request.GET.get("fy")) if request.GET.get("fy") else 0
        except (TypeError, ValueError) as error:
            messages.warning(request, f"{error}, You have provided invalid request.")

        if str(quarter) not in QUARTERKEYS:
            messages.warning(request, "Quarter is invalid.  Either value is missing or outside range")
        if fundcenter and fund and fy:
            query_string = set_query_string(fundcenter, fund, fy, quarter)

    initial = {
        "fundcenter": fundcenter,
        "fund": fund,
        "fy": fy,
        "quarter": quarter,
    }

    if query_string and (CostCenterAllocation.objects.exists() or FundCenterAllocation.objects.exists()):
        r = utils.AllocationStatusReport()
        df = r.allocation_status_dataframe(fundcenter, fund, fy, int(quarter))
        if not df.empty:
            df["Amount"] = df["Amount"].astype(int)
            df["Fiscal Year"] = df["Fiscal Year"].astype(str)
            df = df.style.format(thousands=",")
            # df = r.styler_clean_table(df)
            table = df.to_html()

    form = SearchAllocationAnalysisForm(initial=initial)
    context = {
        "form": form,
        "form_filter": form_filter,
        "initial": initial,
        "query_string": query_string,
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
    report = utils.CostCenterScreeningReport()
    data = report.financial_structure_dataframe()
    if not data.empty:
        data = report.financial_structure_styler(data)
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
