from django.urls import path
from . import views

urlpatterns = [
    path("", views.fund_page, name="fund-page"),
    path("table/", views.fund_page, name="fund-table"),
    path("add/", views.fund_add, name="fund-add"),
    path("update/<int:pk>/", views.fund_update, name="fund-update"),
]
