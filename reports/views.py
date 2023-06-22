from django.core.paginator import Paginator
from django.db.models import Sum
from django.db.models.functions import Concat
from django.db.models import CharField, Value as V
from django.http import HttpResponse
from django.shortcuts import render
import csv

from lineitems.models import LineItem


def bmt_screening_report(request):
    data = (
        LineItem.objects.values("fundcenter", "costcenter", "fund")
        .annotate(
            spent=Sum("spent"),
            wp=Sum("workingplan"),
            balance=Sum("balance"),
            fcst=Sum("fcst__forecastamount"),
        )
        .order_by("fundcenter", "costcenter", "fund")
        .filter(balance__gt=0)
    )
    paginator = Paginator(data, 50)
    page_number = request.GET.get("page")
    context = {"data": paginator.get_page(page_number)}
    return render(request, "bmt-screening-report.html", context)


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


"""
Writes line item report to csv.
"""


def csv_line_items(request):
    data = (
        LineItems.objects.annotate(doc=Concat("docno", V("-"), "lineno"))
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
