from django.shortcuts import render, redirect

from .models import Fund
from .forms import FundForm, SourceForm


def fund_page(request):
    data = Fund.objects.all()
    return render(request, "costcenter/fund-table.html", context={"data": data})


def fund_add(request):
    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            fund = form.save(commit=False)
            fund.fund = fund.fund.upper()
            fund.save()
            return redirect("fund-table")
    else:
        form = FundForm

    return render(request, "costcenter/fund-form.html", {"form": form})


def fund_update(request, pk):
    fund = Fund.objects.get(id=pk)
    form = FundForm(instance=fund)

    if request.method == "POST":
        form = FundForm(request.POST, instance=fund)
        if form.is_valid():
            fund = form.save(commit=False)
            fund.fund = fund.fund.upper()
            fund.save()
            return redirect("funds")

    return render(request, "costcenter/fund-form.html", {"form": form})


def source_add(request):
    if request.method == "POST":
        form = SourceForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.source = obj.source.upper()
            obj.save()
            return redirect("source-table")
    else:
        form = SourceForm

    return render(request, "costcenter/source-form.html", {"form": form})
