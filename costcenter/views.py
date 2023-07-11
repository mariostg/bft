from django.shortcuts import render, redirect
from django.db import IntegrityError
from django.contrib import messages
from .models import (
    Fund,
    Source,
    FundCenter,
    CostCenter,
    CostCenterAllocation,
    ForecastAdjustment,
    FinancialStructureManager,
)
from .forms import (
    FundForm,
    SourceForm,
    FundCenterForm,
    CostCenterForm,
    CostCenterAllocationForm,
    ForecastadjustmentForm,
)
from costcenter.structure import Structure


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
            return redirect("fund-table")

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
    return render(request, "costcenter/source-table.html", context={"sources": data})
    return render(request, "costcenter/source-table.html", context={"sources": data})


def source_add(request):
    if request.method == "POST":
        form = SourceForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "Saving this record would create duplicate entry.")
                return render(request, "costcenter/source-form.html", {"form": form})
            return redirect("source-table")
    else:
        form = SourceForm

    return render(request, "costcenter/source-form.html", {"form": form})


def source_update(request, pk):
    source = Source.objects.pk(pk)
    form = SourceForm(instance=source)

    if request.method == "POST":
        form = SourceForm(request.POST, instance=source)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(request, "Saving this record would create duplicate entry.")
                return render(request, "costcenter/source-form.html", {"form": form})
            return redirect("source-table")

    return render(request, "costcenter/source-form.html", {"form": form})


def source_delete(request, pk):
    source = Source.objects.pk(pk)
    if request.method == "POST":
        source.delete()
        return redirect("source-table")
    context = {"object": source, "back": "source-table"}
    return render(request, "core/delete-object.html", context)


def fundcenter_page(request):
    data = FundCenter.objects.all()
    return render(request, "costcenter/fundcenter-table.html", context={"fundcenters": data})


def fundcenter_costcenters(request, pk):
    data = CostCenter.objects.filter(parent=pk)
    return render(request, "costcenter/costcenter-table.html", {"data": data})


def fundcenter_add(request):
    if request.method == "POST":
        form = FundCenterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)

            fsm = FinancialStructureManager()
            obj.sequence = fsm.set_parent(fundcenter_parent=obj.parent, fundcenter_child=obj)
            obj.save()
            return redirect("fundcenter-table")
    else:
        form = FundCenterForm

    return render(request, "costcenter/fundcenter-form.html", {"form": form})


def fundcenter_update(request, pk):
    fundcenter = FundCenter.objects.get(id=pk)
    form = FundCenterForm(instance=fundcenter)

    if request.method == "POST":
        form = FundCenterForm(request.POST, instance=fundcenter)
        if form.is_valid():
            form.save()
            return redirect("fundcenter-table")
        else:
            print("NOT VALID")
    return render(request, "costcenter/fundcenter-form.html", {"form": form})


def fundcenter_delete(request, pk):
    fundcenter = FundCenter.objects.get(id=pk)
    if request.method == "POST":
        fundcenter.delete()
        return redirect("fundcenter-table")
    context = {"object": fundcenter, "back": "fundcenter-table"}
    return render(request, "core/delete-object.html", context)


def costcenter_page(request):
    data = CostCenter.objects.all()
    return render(request, "costcenter/costcenter-table.html", context={"data": data})


def costcenter_add(request):
    if request.method == "POST":
        form = CostCenterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.costcenter = obj.costcenter.upper()
            if obj.shortname:
                obj.shortname = obj.shortname.upper()
            obj.save()
            return redirect("costcenter-table")
    else:
        form = CostCenterForm

    return render(request, "costcenter/costcenter-form.html", {"form": form})


def costcenter_update(request, pk):
    costcenter = CostCenter.objects.pk(pk=pk)
    form = CostCenterForm(instance=costcenter)

    if request.method == "POST":
        form = CostCenterForm(request.POST, instance=costcenter)
        if form.is_valid():
            form.save()
            return redirect("costcenter-table")

    return render(request, "costcenter/costcenter-form.html", {"form": form})


def costcenter_delete(request, pk):
    costcenter = CostCenter.objects.get(id=pk)
    if request.method == "POST":
        costcenter.delete()
        return redirect("costcenter-table")
    context = {"object": costcenter, "back": "costcenter-table"}
    return render(request, "core/delete-object.html", context)


def costcenter_allocation_page(request):
    data = CostCenterAllocation.objects.all()
    if data.count() == 0:
        messages.info(request, "There are no Allocations.")
    return render(request, "costcenter/costcenter-allocation-table.html", {"data": data})


def costcenter_allocation_add(request):
    if request.method == "POST":
        form = CostCenterAllocationForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.user = request.user
            form.save()
            return redirect("costcenter-allocation-table")
    else:
        form = CostCenterAllocationForm

    return render(request, "costcenter/costcenter-allocation-form.html", {"form": form})


def costcenter_allocation_update(request, pk):
    data = CostCenterAllocation.objects.get(id=pk)
    form = CostCenterAllocationForm(instance=data)
    if request.method == "POST":
        form = CostCenterAllocationForm(request.POST, instance=data)
        if form.is_valid():
            form = form.save(commit=False)
            form.owner = request.user
            form.save()
            return redirect("costcenter-allocation-table")

    return render(request, "costcenter/costcenter-allocation-form.html", {"form": form})


def costcenter_allocation_delete(request, pk):
    item = CostCenterAllocation.objects.get(id=pk)
    if request.method == "POST":
        item.delete()
        return redirect("costcenter-allocation-table")
    context = {"object": item, "back": "costcenter-allocation-table"}
    return render(request, "core/delete-object.html", context)


def forecast_adjustment_page(request):
    data = ForecastAdjustment.objects.all()
    if data.count() == 0:
        messages.info(request, "There are no forecast adjustment.")
    context = {"data": data}
    return render(request, "costcenter/forecast-adjustment-table.html", context)


# @login_required
def forecast_adjustment_add(request):
    if request.method == "POST":
        form = ForecastadjustmentForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.user = request.user
            form.save()
            return redirect("forecast-adjustment-table")
    else:
        form = ForecastadjustmentForm

    return render(request, "costcenter/forecast-adjustment-form.html", {"form": form})


# @login_required
def forecast_adjustment_update(request, pk):
    forecastadjustment = ForecastAdjustment.objects.get(id=pk)
    form = ForecastadjustmentForm(instance=forecastadjustment)

    if request.method == "POST":
        form = ForecastadjustmentForm(request.POST, instance=forecastadjustment)
        if form.is_valid():
            form = form.save(commit=False)
            form.owner = request.user
            form.save()
            return redirect("forecast-adjustment-table")

    return render(request, "costcenter/forecast-adjustment-form.html", {"form": form})


# @login_required
def forecast_adjustment_delete(request, pk):
    item = ForecastAdjustment.objects.get(id=pk)
    if request.method == "POST":
        item.delete()
        return redirect("forecast-adjustment-table")
    context = {"object": item, "back": "forecast-adjustment-table"}
    return render(request, "core/delete_object.html", context)
