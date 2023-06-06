from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from .models import LineItem, LineForecast
from utils import searchlines
from .forms import LineForecastForm, SearchLineItemForm


def lineitem_page(request):
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
            return redirect("lineitem-table")
    else:
        form = LineForecastForm()
    return render(
        request,
        "lineitems/line-forecast-form.html",
        {"form": form, "lineitem": lineitem},
    )
