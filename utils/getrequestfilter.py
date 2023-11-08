from lineitems.models import LineItem
from costcenter.models import FundCenterAllocation, CostCenterAllocation

"""
Search line items from GET request based on cost center, fund and document type.
"""


def search_lines(request):
    costcenter = fund = doctype = linetext = status = ""
    has_forecast = has_workingplan = createdby = ""
    query_string = ""
    data = LineItem.objects.all()
    query_terms = set()
    if request.GET.get("costcenter"):
        costcenter = request.GET.get("costcenter").upper()
        query_terms.add(f"costcenter={costcenter}")
        data = data.filter(
            costcenter__costcenter__exact=costcenter,
        )
    if request.GET.get("fund"):
        fund = request.GET.get("fund").upper()
        query_terms.add(f"fund={fund}")
        data = data.filter(
            fund__exact=fund,
        )
    if request.GET.get("doctype"):
        doctype = request.GET.get("doctype").upper()
        query_terms.add(f"doctype={doctype}")
        data = data.filter(
            doctype__exact=doctype,
        )
    if request.GET.get("docno"):
        docno = request.GET.get("docno")
        query_terms.add(f"doctype={docno}")
        data = data.filter(
            docno__exact=docno,
        )
    if request.GET.get("linetext"):
        linetext = request.GET.get("linetext")
        query_terms.add(f"linetext={linetext}")
        data = data.filter(
            linetext__icontains=linetext,
        )
    if request.GET.get("createdby"):
        createdby = request.GET.get("createdby")
        query_terms.add(f"createdby={createdby}")
        data = data.filter(
            createdby__icontains=createdby,
        )
    if request.GET.get("status"):
        status = request.GET.get("status").capitalize()
        data = data.filter(
            status__exact=status,
        )
    if request.GET.get("has_forecast"):
        has_forecast = request.GET.get("has_forecast")
        query_terms.add(f"has_forecast={has_forecast}")
        data = data.filter(
            fcst__forecastamount__gt=0,
        )
    if request.GET.get("has_workingplan"):
        has_workingplan = request.GET.get("has_workingplan")
        query_terms.add(f"has_workingplan={has_workingplan}")
        data = data.filter(
            workingplan__gt=0,
        )
    if request.GET.get("createdby"):
        createdby = request.GET.get("createdby")
        query_terms.add(f"has_workingplan={createdby}")
        data = data.filter(
            createdby__contains=createdby,
        )
    initial = {
        "costcenter": costcenter,
        "fund": fund,
        "doctype": doctype,
        "linetext": linetext,
        "status": status,
        "has_forecast": has_forecast,
        "has_workingplan": has_workingplan,
        "createdby": createdby,
    }
    if len(query_terms) > 0:
        query_string = "&".join(query_terms)

    return data, initial, query_string


def set_query_string(**kwargs) -> str:
    query_string = ""
    query_terms = set()
    for item in kwargs:
        query_terms.add(f"{item}={kwargs[item]}")
    if len(query_terms) > 0:
        query_string = "&".join(query_terms)
    return query_string
