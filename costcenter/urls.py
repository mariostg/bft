from django.urls import path
from . import views

urlpatterns = [
    path("", views.fund_page, name="fund-table"),
    path("fund-table/", views.fund_page, name="fund-table"),
    path("fund-add/", views.fund_add, name="fund-add"),
    path("fund-update/<int:pk>/", views.fund_update, name="fund-update"),
    path("source-table/", views.source_page, name="source-table"),
    path("source-add/", views.source_add, name="source-add"),
]
