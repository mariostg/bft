from django.core.paginator import Paginator
from django.db.models import Sum
from django.db.models.functions import Concat
from django.db.models import CharField, Value as V
from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
import csv

from lineitems.models import LineItem
from reports import utils
from costcenter.models import CostCenterAllocation, ForecastAdjustment, FundCenterAllocation


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
    context = {}
    if CostCenterAllocation.objects.exists() or FundCenterAllocation.objects.exists():
        r = utils.AllocationReport()
        df = r.allocation_status_dataframe()
        df["Allocation"] = df["Allocation"].astype(int)
        df["FY"] = df["FY"].astype(str)
        df = df.style.format(thousands=",")
        # df = r.styler_clean_table(df)
        context = {"table": df.to_html()}
    return render(request, "allocation-status-report.html", context)


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
