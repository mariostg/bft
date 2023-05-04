from django.shortcuts import render, HttpResponse

from .models import Fund


def fund_page(request):
    data = Fund.objects.all()
    return render(request, "costcenter/fund-page.html", context={"data": data})


def fund_new(request):
    if request.method == "POST":
        data = request.POST
        fund = Fund(**data)
        fund.save()
    return HttpResponse("Visited fund_new view")
