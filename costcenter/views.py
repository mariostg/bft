from django.shortcuts import render, redirect

from .models import Fund, Source, FundCenter, CostCenter
from .forms import FundForm, SourceForm, FundCenterForm, CostCenterForm


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


def fund_delete(request, pk):
    fund = Fund.objects.get(id=pk)
    if request.method == "POST":
        fund.delete()
        return redirect("fund-table")
    context = {"object": fund, "back": "fund-table"}
    return render(request, "core/delete-object.html", context)


def source_page(request):
    data = Source.objects.all()
    return render(request, "costcenter/source-table.html", context={"data": data})


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


def fundcenter_page(request):
    data = FundCenter.objects.all()
    return render(request, "costcenter/fundcenter-table.html", context={"data": data})


def fundcenter_add(request):
    if request.method == "POST":
        form = FundCenterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.fundcenter = obj.fundcenter.upper()
            obj.shortname = obj.shortname.upper()
            obj.save()
            return redirect("fundcenter-table")
    else:
        form = FundCenterForm

    return render(request, "costcenter/fundcenter-form.html", {"form": form})


def costcenter_page(request):
    data = CostCenter.objects.all()
    return render(request, "costcenter/costcenter-table.html", context={"data": data})


def costcenter_add(request):
    if request.method == "POST":
        form = CostCenterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.costcenter = obj.costcenter.upper()
            obj.shortname = obj.shortname.upper()
            obj.save()
            return redirect("costcenter-table")
    else:
        form = CostCenterForm

    return render(request, "costcenter/costcenter-form.html", {"form": form})


def costcenter_update(request, pk):
    costcenter = CostCenter.objects.get(id=pk)
    form = CostCenterForm(instance=costcenter)

    if request.method == "POST":
        form = CostCenterForm(request.POST, instance=costcenter)
        if form.is_valid():
            form.save()
            return redirect("costcenter-page")

    return render(request, "costcenters/costcenter-form.html", {"form": form})
