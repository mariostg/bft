from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView

from bft.conf import PERIODS, QUARTERS
from bft.forms import BftStatusForm
from bft.models import BftStatus


class HomeView(TemplateView):
    template_name = "bft/bft.html"


def bft_status(request):
    url_name = "bft-status"
    status = BftStatus.current
    fy = status.fy()
    try:
        quarter = QUARTERS[int(status.quarter())][1]
    except TypeError:
        quarter = None
    try:
        period = PERIODS[int(status.period()) - 1][1]
    except TypeError:
        period = None

    return render(
        request,
        f"bft/{url_name}.html",
        {"fy": fy, "quarter": quarter, "period": period, "url_name": url_name, "title": "BFT Status"},
    )


def ajax_status_request(request):
    status = BftStatus.current
    fy = status.fy()
    # Data
    d = {"Fy": fy, "period": status.period(), "quarter": status.quarter()}
    return JsonResponse(d)


def _bft_status_update(request, status):
    try:
        data = BftStatus.objects.get(status=status)
    except BftStatus.DoesNotExist:
        data = BftStatus(status=status, value=None)
    form = BftStatusForm(instance=data)

    if request.method == "POST":
        form = BftStatusForm(request.POST, instance=data)
        if form.is_valid():
            try:
                form.save()
                return redirect("bft-status")
            except ValueError as err:
                messages.warning(request, err)
                return render(
                    request, f"bft/{status.lower()}-form.html", {"form": form}
                )
    return render(request, f"bft/{status.lower()}-form.html", {"form": form})


def bft_fy_update(request):
    return _bft_status_update(request, "FY")


def bft_quarter_update(request):
    return _bft_status_update(request, "QUARTER")


def bft_period_update(request):
    return _bft_status_update(request, "PERIOD")
