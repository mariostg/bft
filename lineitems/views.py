from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F
from django.db.models.lookups import GreaterThan
from django.core.paginator import Paginator
import logging
from .models import LineItem, LineForecast
from costcenter.models import CostCenter
from .forms import LineForecastForm, DocumentNumberForm, CostCenterForecastForm, CostCenterLineItemUploadForm
from lineitems.filters import LineItemFilter
from lineitems.forms import FundCenterLineItemUploadForm
from main.settings import UPLOADS
from bft.uploadprocessor import LineItemProcessor, CostCenterLineItemProcessor

logger = logging.getLogger("django")


def document_page(request, docno):
    lines = LineItem.objects.filter(docno=docno)
    paginator = Paginator(lines, 25)
    page_number = request.GET.get("page")
    context = {
        "data": paginator.get_page(page_number),
    }
    return render(request, "lineitems/lineitem-table.html", context)


def lineitem_page(request):
    has_filter = False
    if not request.GET:
        data = LineItem.objects.none()
    else:
        data = (
            LineItem.objects.all()
            .order_by("docno")
            .annotate(wp_rising=GreaterThan(F("workingplan"), F("fcst__workingplan_initial")))
        )
        has_filter = True
    search_filter = LineItemFilter(request.GET, queryset=data)
    return render(
        request,
        "lineitems/lineitem-table.html",
        {"filter": search_filter, "has_filter": has_filter, "reset": "lineitem-page"},
    )


def line_forecast_add(request, pk):
    lineitem = LineItem.objects.get(pk=pk)
    if request.method == "POST":
        form = LineForecastForm(request.POST)
        if form.is_valid():
            line_forecast = form.save(commit=False)
            line_forecast.lineitem_id = pk  # LineItems(id=pk)
            if line_forecast.above_working_plan(request, lineitem):
                line_forecast.forecastamount = lineitem.workingplan
                messages.info(
                    request, f"Forecast above working plan, created with amount of {lineitem.workingplan}"
                )
            elif line_forecast.below_spent(request, lineitem):
                line_forecast.forecastamount = lineitem.spent
                messages.info(request, f"Forecast below spent, created with amount of {lineitem.spent}")
            else:
                messages.success(request, "Forecast created")
            line_forecast.save()
            return redirect("lineitem-page")
    else:
        form = LineForecastForm()
    return render(
        request,
        "lineitems/line-forecast-form.html",
        {"form": form, "lineitem": lineitem},
    )


def line_forecast_update(request, pk):
    data = get_object_or_404(LineForecast, pk=pk)
    working_plan = data.lineitem.workingplan
    spent = data.lineitem.spent
    form = LineForecastForm(instance=data)
    if request.method == "POST":
        form = LineForecastForm(request.POST, instance=data)
        if form.is_valid():
            form = form.save(commit=False)
            forecast_amount = form.forecastamount
            if form.forecastamount < spent:
                messages.warning(
                    request,
                    f"Forecast {forecast_amount}  cannot be lower than Spent {spent}. Forecast set to {spent}",
                )
                form.forecastamount = spent
            elif form.forecastamount > working_plan:
                messages.warning(
                    request,
                    f"Forecast {forecast_amount} cannot be higher than working plan {working_plan}.  Forecast set to {working_plan}.",
                )
                form.forecastamount = working_plan
            else:
                messages.success(request, "Forecast has been updated")
                # form.owner = request.user
            form.save()
            return redirect("lineitem-page")

    return render(request, "lineitems/line-forecast-form.html", {"form": form, "lineitem": data.lineitem})


def line_forecast_to_wp_update(request, pk):
    if request.method == "GET":
        target = LineForecast.objects.get(pk=pk)
        target.forecastamount = target.lineitem.workingplan
        target.save()
        messages.info(request, "Forecast set to working plan amount")
    return redirect("lineitem-page")


def line_forecast_zero_update(request, pk):
    if request.method == "GET":
        target = LineForecast.objects.get(pk=pk)
        if target.lineitem.spent > 0:
            messages.warning(request, "Cannot set forecast to 0 when Spent is greater than 0")
        else:
            target.forecastamount = 0
            target.save()
            messages.success(request, "Forecast has been set to 0")
    return redirect("lineitem-page")


def line_forecast_delete(request, pk):
    target = LineForecast.objects.get(pk=pk)

    if request.method == "POST":
        if target.lineitem.spent > 0:
            messages.warning(request, "Cannot delete forecast when Spent is greater than 0")
        else:
            messages.success(request, "Forecast has been deleted")
            target.delete()
        return redirect("lineitem-page")
    context = {"object": "Forecast for " + target.lineitem.linetext, "back": "lineitem-page"}
    return render(request, "core/delete-object.html", context)


def line_item_delete(request, pk):
    """A line item can be delete when the working plan is zero.  By definition, it means that
    the line item is no longer in DRMIS encumbrance report.
    In addition, a line item can only be deleted if the current user is the procurement officer assigned to the cost center le line item belongs to.
    """
    target = LineItem.objects.get(pk=pk)

    if target.costcenter.procurement_officer != request.user:
        messages.warning(request, "Only owner can delete a line item.")
        return redirect("lineitem-page")

    if request.method == "POST":
        if target.costcenter.procurement_officer != request.user:
            messages.warning(request, "Only owner can delete a line item.")
        else:
            messages.success(request, f"line item {target.linetext} has been deleted")
            target.delete()
        return redirect("lineitem-page")

    context = {
        "object": target.linetext,
        "back": "lineitem-page",
    }
    return render(request, "core/delete-object.html", context)

    print(
        f"Created by {target.createdby}, \n current user is {request.user},\n forecast owner is {target.fcst.owner}, \n procurement cost center owner {target.costcenter.procurement_officer}"
    )
    if target.costcenter.procurement_officer == request.user:
        print(f"This is the current user {request.user}.  Owner is {target.costcenter.procurement_officer}")
        context = {
            "object": "Line item target to delete " + target.linetext,
            "back": "lineitem-page",
        }
        return render(request, "core/delete-object.html", context)

    else:
        messages.warning(request, "Only owner can delete a line item.")
    return redirect("lineitem-page")


def fundcenter_lineitem_upload(request):
    if request.method == "POST":
        form = FundCenterLineItemUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            filepath = f"{UPLOADS}/lineitem-upload-{user}.csv"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = LineItemProcessor(filepath, request)
            processor.main()
    else:
        form = FundCenterLineItemUploadForm
    return render(
        request, "lineitems/fundcenter-lineitem-upload-form.html", {"form": form, "form_title": "Fund Upload"}
    )


def costcenter_lineitem_upload(request):
    """This function handles the uploading of line items for a given cost center.  This means that the encumbrance must contain only one cost center and one fund center."""
    if request.method == "POST":
        form = CostCenterLineItemUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            fundcenter = request.POST.get("fundcenter")
            costcenter = request.POST.get("costcenter")
            print("DATA:", fundcenter, costcenter)
            filepath = f"{UPLOADS}/lineitem-upload-{user}.csv"
            with open(filepath, "wb+") as destination:
                for chunk in request.FILES["source_file"].chunks():
                    destination.write(chunk)
            processor = CostCenterLineItemProcessor(filepath, costcenter, fundcenter, request)
            processor.main()
    else:
        form = CostCenterLineItemUploadForm
    return render(
        request, "lineitems/costcenter-lineitem-upload-form.html", {"form": form, "form_title": "Fund Upload"}
    )


def document_forecast(request, docno):
    context = {"back": "lineitem-page"}
    context["docno"] = docno
    if request.method == "POST":
        form = DocumentNumberForm(request.POST)
        if form.is_valid():
            docno = request.POST.get("docno")
            forecast = request.POST.get("forecastamount")
            lf = LineForecast().forecast_line_by_line(docno, float(forecast))
            return redirect(reverse("lineitem-page") + f"?docno__iexact={docno}")
    doc = LineItem.objects.filter(docno=docno)
    agg = doc.aggregate(Sum("workingplan"), Sum("spent"))
    agg["workingplan__sum"] = round(agg["workingplan__sum"], 2)
    agg["spent__sum"] = round(agg["spent__sum"], 2)
    form = DocumentNumberForm(
        initial={
            "docno": docno,
            "forecastamount": agg["workingplan__sum"],
        }
    )
    context["form"] = form
    context["agg"] = agg
    if doc.count() == 0:
        messages.warning(request, f"Requested document number was not found : {docno} ")
    return render(request, "lineitems/document-item-forecast-form.html", context)


def costcenter_forecast(request, costcenter_pk):
    context = {"back": "lineitem-page"}
    context["costcenter_pk"] = costcenter_pk
    costcenter = CostCenter.objects.get(pk=costcenter_pk)
    if request.method == "POST":
        form = CostCenterForecastForm(request.POST)
        if form.is_valid():
            costcenter_pk = request.POST.get("costcenter_pk")
            forecast = request.POST.get("forecastamount")
            LineForecast().forecast_costcenter_lines(costcenter_pk, float(forecast))
            return redirect(reverse("lineitem-page") + f"?costcenter={costcenter_pk}")
    doc = LineItem.objects.filter(costcenter=costcenter_pk)
    agg = doc.aggregate(Sum("workingplan"), Sum("spent"))
    agg["workingplan__sum"] = round(agg["workingplan__sum"], 2)
    agg["spent__sum"] = round(agg["spent__sum"], 2)
    form = CostCenterForecastForm(
        initial={
            "costcenter_pk": costcenter_pk,
            "forecastamount": agg["workingplan__sum"],
        }
    )
    context["form"] = form
    context["agg"] = agg
    context["costcenter"] = costcenter
    if doc.count() == 0:
        messages.warning(request, f"Requested cost center was not found : {costcenter} ")
    return render(request, "lineitems/costcenter-item-forecast-form.html", context)
