from django.urls import path
from . import views

urlpatterns = [
    path("fund_page/", views.fund_page, name="fund-page"),
    path("add/", views.fund_add, name="fund-add"),
]
