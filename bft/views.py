from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect

from bft.models import BftStatus
from bft.conf import QUARTERS, PERIODS
from bft.forms import BftForm


class HomeView(TemplateView):
    template_name = "bft/bft.html"


def bft_status(request):
    status = BftStatus.current
    fy = status.fy()
    quarter = QUARTERS[int(status.quarter())][1]
    period = PERIODS[int(status.period()) - 1][1]

    return render(request, "bft/bft-status.html", {"fy": fy, "quarter": quarter, "period": period})


def bft_fy_update(request):
    data = BftStatus.objects.get(status="FY")
    form = BftForm(instance=data)

    if request.method == "POST":
        form = BftForm(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return redirect("bft-status")

    return render(request, "bft/fy-form.html", {"form": form})


def bft_quarter_update(request):
    data = BftStatus.objects.get(status="QUARTER")
    form = BftForm(instance=data)

    if request.method == "POST":
        form = BftForm(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return redirect("bft-status")

    return render(request, "bft/quarter-form.html", {"form": form})


def bft_period_update(request):
    data = BftStatus.objects.get(status="PERIOD")
    form = BftForm(instance=data)

    if request.method == "POST":
        form = BftForm(request.POST, instance=data)
        if form.is_valid():
            form.save()
            return redirect("bft-status")

    return render(request, "bft/period-form.html", {"form": form})
