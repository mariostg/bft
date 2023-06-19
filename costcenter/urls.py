from django.urls import path
from . import views

urlpatterns = [
    path("", views.fund_page, name="fund-table"),
]
urlpatterns += [
    path("fund-table/", views.fund_page, name="fund-table"),
    path("fund-add/", views.fund_add, name="fund-add"),
    path("fund-update/<int:pk>/", views.fund_update, name="fund-update"),
    path("fund-delete/<int:pk>/", views.fund_delete, name="fund-delete"),
]

urlpatterns += [
    path("source-table/", views.source_page, name="source-table"),
    path("source-add/", views.source_add, name="source-add"),
    path("source-update/<int:pk>/", views.source_update, name="source-update"),
    path("source-delete/<int:pk>/", views.source_delete, name="source-delete"),
]

urlpatterns += [
    path("fundcenter/<int:pk>/costcenters/", views.fundcenter_costcenters, name="fundcenter-costcenters"),
    path("fundcenter-table/", views.fundcenter_page, name="fundcenter-table"),
    path("fundcenter-add/", views.fundcenter_add, name="fundcenter-add"),
    path("fundcenter-update/<int:pk>", views.fundcenter_update, name="fundcenter-update"),
    path("fundcenter-delete/<int:pk>", views.fundcenter_delete, name="fundcenter-delete"),
]

urlpatterns += [
    path("costcenter-table/", views.costcenter_page, name="costcenter-table"),
    path("costcenter-add/", views.costcenter_add, name="costcenter-add"),
    path("costcenter-update/<int:pk>", views.costcenter_update, name="costcenter-update"),
]

urlpatterns += [
    path("allocation-table/", views.allocation_page, name="costcenter-allocation-table"),
    path("allocation-add/", views.allocation_add, name="costcenter-allocation-add"),
]

urlpatterns += [
    path("forecast-adjustment-table", views.forecast_adjustment_page, name="forecast-adjustment-table"),
    path("forecast-adjustment-add", views.forecast_adjustment_add, name="forecast-adjustment-add"),
]
