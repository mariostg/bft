from django.shortcuts import render, redirect

from .models import Fund
from .forms import FundForm


def fund_page(request):
    data = Fund.objects.all()
    return render(request, "costcenter/fund-page.html", context={"data": data})


def fund_add(request):
    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            fund = form.save(commit=False)
            fund.fund = fund.fund.upper()
            fund.save()
            return redirect("fund-page")
    else:
        form = FundForm

    return render(request, "costcenter/fund-form.html", {"form": form})
