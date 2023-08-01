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
    path("fundcenter-allocation-table/", views.fundcenter_allocation_page, name="fundcenter-allocation-table"),
    path("fundcenter-allocation-add/", views.fundcenter_allocation_add, name="fundcenter-allocation-add"),
    path(
        "fundcenter-allocation-update/<int:pk>", views.fundcenter_allocation_update, name="fundcenter-allocation-update"
    ),
    path(
        "fundcenter-allocation-delete/<int:pk>", views.fundcenter_allocation_delete, name="fundcenter-allocation-delete"
    ),
]

urlpatterns += [
    path("costcenter-table/", views.costcenter_page, name="costcenter-table"),
    path("costcenter-add/", views.costcenter_add, name="costcenter-add"),
    path("costcenter-update/<int:pk>", views.costcenter_update, name="costcenter-update"),
    path("costcenter-delete/<int:pk>", views.costcenter_delete, name="costcenter-delete"),
]

urlpatterns += [
    path("costcenter-allocation-table/", views.costcenter_allocation_page, name="costcenter-allocation-table"),
    path("costcenter-allocation-add/", views.costcenter_allocation_add, name="costcenter-allocation-add"),
    path(
        "costcenter-allocation-update/<int:pk>", views.costcenter_allocation_update, name="costcenter-allocation-update"
    ),
    path(
        "costcenter-allocation-delete/<int:pk>", views.costcenter_allocation_delete, name="costcenter-allocation-delete"
    ),
]

urlpatterns += [
    path("forecast-adjustment-table", views.forecast_adjustment_page, name="forecast-adjustment-table"),
    path("forecast-adjustment-add", views.forecast_adjustment_add, name="forecast-adjustment-add"),
    path("forecast-adjustment-update/<int:pk>", views.forecast_adjustment_update, name="forecast-adjustment-update"),
    path("forecast-adjustments-delete/<int:pk>", views.forecast_adjustment_delete, name="forecast-adjustment-delete"),
]
