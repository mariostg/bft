from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
import logging
from .models import LineItem, LineForecast
from utils import searchlines
from .forms import LineForecastForm, SearchLineItemForm

logger = logging.getLogger("django")


def lineitem_page(request):
    logger.info("Visiting Line Item page as info")
    print("%%%%%%%%%%%%%")
    lines, initial, query_string = searchlines.search_lines(request)
    paginator = Paginator(lines, 25)
    page_number = request.GET.get("page")
    form = SearchLineItemForm(initial=initial)
    context = {
        "data": paginator.get_page(page_number),
        "form": form,
        "initial": initial,
        "query_string": query_string,
    }
    return render(request, "lineitems/lineitem-table.html", context)


def line_forecast_add(request, pk):
    lineitem = LineItem.objects.get(pk=pk)
    if request.method == "POST":
        form = LineForecastForm(request.POST)
        if form.is_valid():
            line_forecast = form.save(commit=False)
            line_forecast.lineitem_id = pk  # LineItems(id=pk)
            if line_forecast.validate(request, lineitem) == False:
                form.forecastamount = lineitem.workingplan
                messages.info(request, f"Forecast created with amount of {lineitem.workingplan}")
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
    target = LineItem.objects.get(pk=pk)
    if target.createdby == request.user:
        print(f"This is the current user {request.user}.  Owner is {target.createdby}")
    else:
        messages.warning(request, "Only owner can delete a line item.")
    return redirect("lineitem-page")


def costcenter_lineitems(request, costcenter):
    data = LineItem.objects.cost_center(costcenter)
    if not data:
        messages.info(request, f"There appears to be no line items in {costcenter}")
    context = {"data": data}
    return render(request, "lineitems/lineitem-table.html", context)
