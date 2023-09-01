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
    fundcenter = fund = fy = quarter = ""
    query_string = None  # Keep query_string in case paginator is required when more data is used.
    query_terms = set()
    context = {}
    table = None

    fundcenter = FundCenterManager().get_request(request)

    fund = FundManager().get_request(request)

    quarter = request.GET.get("quarter")
    if quarter in ["0", "1", "2", "3", "4"]:
        quarter = f"Q{quarter}"
    if quarter in ["q0", "q1", "q2", "q3", "q4", "Q0", "Q1", "Q2", "Q3", "Q4"]:
        quarter = quarter.upper()

    fy = request.GET.get("fy")

    if fundcenter and fund and fy and quarter:
        query_terms.add(f"fundcenter={fundcenter}")
        query_terms.add(f"fund={fund}")
        query_terms.add(f"quarter={quarter}")
        query_terms.add(f"fy={fy}")
        if quarter not in ["Q0", "Q1", "Q2", "Q3", "Q4"]:
            messages.warning(request, "Quarter is invalid.  Either value is missing or outside range")

    initial = {
        "fundcenter": fundcenter,
        "fund": fund,
        "fy": fy,
        "quarter": quarter,
    }
    if len(query_terms) > 0:
        query_string = "&".join(query_terms)

    if query_string and (CostCenterAllocation.objects.exists() or FundCenterAllocation.objects.exists()):
        r = utils.AllocationReport()
        df = r.allocation_status_dataframe(fundcenter, fund, fy, quarter)
        if not df.empty:
            df["Allocation"] = df["Allocation"].astype(int)
            df["FY"] = df["FY"].astype(str)
            df = df.style.format(thousands=",")
            # df = r.styler_clean_table(df)
            table = df.to_html()

    form = form = SearchAllocationAnalysisForm(initial=initial)
    context = {
        "form": form,
        "initial": initial,
        "query_string": query_string,
        "table": table,
    }

    return render(request, "allocation-status-report.html", context)


def costcenter_monthly_data(request):
    s = BftStatus.current
    r = utils.CostCenterMonthlyReport(fy=s.fy(), period=s.period())
    df = r.dataframe()

    for c in CostCenterMonthly._meta.get_fields():
        if c.get_internal_type() == "DecimalField":
            df[c.verbose_name] = df[c.verbose_name].astype(int)
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
