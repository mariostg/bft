from django.urls import path
from . import views

urlpatterns = [
    path("", views.fund_page, name="fund-page"),
    path("fund-page/", views.fund_page, name="fund-page"),
    path("add/", views.fund_add, name="fund-add"),
]
