from django.shortcuts import render, HttpResponse

from .models import Fund


def fund_page(request):
    return HttpResponse("<html><title>Fund list</title></html>")


def fund_new(request):
    if request.method == "POST":
        data = request.POST
        fund = Fund(**data)
        fund.save()
    return HttpResponse("Visited fund_new view")
