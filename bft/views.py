from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from django.contrib import messages
from bft.models import BftStatus
from bft.conf import QUARTERS, PERIODS
from bft.forms import BftStatusForm


class HomeView(TemplateView):
    template_name = "bft/bft.html"


def bft_status(request):
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

    return render(request, "bft/bft-status.html", {"fy": fy, "quarter": quarter, "period": period})


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
                return render(request, f"bft/{status.lower()}-form.html", {"form": form})
    return render(request, f"bft/{status.lower()}-form.html", {"form": form})


def bft_fy_update(request):
    return _bft_status_update(request, "FY")


def bft_quarter_update(request):
    return _bft_status_update(request, "QUARTER")


def bft_period_update(request):
    return _bft_status_update(request, "PERIOD")
