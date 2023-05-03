from django.shortcuts import render, HttpResponse


# Create your views here.
def fund_page(request):
    return HttpResponse("<html><title>Fund list</title></html>")
