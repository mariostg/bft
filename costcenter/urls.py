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
    path("fund-upload", views.fund_upload, name="fund-upload"),
]

urlpatterns += [
    path("source-table/", views.source_page, name="source-table"),
    path("source-add/", views.source_add, name="source-add"),
    path("source-update/<int:pk>/", views.source_update, name="source-update"),
    path("source-delete/<int:pk>/", views.source_delete, name="source-delete"),
    path("source-upload", views.source_upload, name="source-upload"),
]

urlpatterns += [
    path("fundcenter-table/", views.fundcenter_page, name="fundcenter-table"),
    path("fundcenter-add/", views.fundcenter_add, name="fundcenter-add"),
    path("fundcenter-update/<int:pk>", views.fundcenter_update, name="fundcenter-update"),
    path("fundcenter-delete/<int:pk>", views.fundcenter_delete, name="fundcenter-delete"),
    path("fundcenter-upload", views.fundcenter_upload, name="fundcenter-upload"),
]

urlpatterns += [
    path(
        "fundcenter-allocation-table/", views.fundcenter_allocation_page, name="fundcenter-allocation-table"
    ),
    path("fundcenter-allocation-add/", views.fundcenter_allocation_add, name="fundcenter-allocation-add"),
    path(
        "fundcenter-allocation-update/<int:pk>",
        views.fundcenter_allocation_update,
        name="fundcenter-allocation-update",
    ),
    path(
        "fundcenter-allocation-delete/<int:pk>",
        views.fundcenter_allocation_delete,
        name="fundcenter-allocation-delete",
    ),
    path(
        "fundcenter-allocation-upload",
        views.fundcenter_allocation_upload,
        name="fundcenter-allocation-upload",
    ),
]

urlpatterns += [
    path("costcenter-table/", views.costcenter_page, name="costcenter-table"),
    path("costcenter-add/", views.costcenter_add, name="costcenter-add"),
    path("costcenter-update/<int:pk>", views.costcenter_update, name="costcenter-update"),
    path("costcenter-delete/<int:pk>", views.costcenter_delete, name="costcenter-delete"),
    path("costcenter-upload", views.costcenter_upload, name="costcenter-upload"),
]

urlpatterns += [
    path(
        "costcenter-allocation-table/", views.costcenter_allocation_page, name="costcenter-allocation-table"
    ),
    path("costcenter-allocation-add/", views.costcenter_allocation_add, name="costcenter-allocation-add"),
    path(
        "costcenter-allocation-update/<int:pk>",
        views.costcenter_allocation_update,
        name="costcenter-allocation-update",
    ),
    path(
        "costcenter-allocation-delete/<int:pk>",
        views.costcenter_allocation_delete,
        name="costcenter-allocation-delete",
    ),
    path(
        "costcenter-allocation-upload",
        views.costcenter_allocation_upload,
        name="costcenter-allocation-upload",
    ),
]

urlpatterns += [
    path("forecast-adjustment-table", views.forecast_adjustment_page, name="forecast-adjustment-table"),
    path("forecast-adjustment-add", views.forecast_adjustment_add, name="forecast-adjustment-add"),
    path(
        "forecast-adjustment-update/<int:pk>",
        views.forecast_adjustment_update,
        name="forecast-adjustment-update",
    ),
    path(
        "forecast-adjustments-delete/<int:pk>",
        views.forecast_adjustment_delete,
        name="forecast-adjustment-delete",
    ),
]

urlpatterns += [
    path("capital-project-table/", views.capital_project_page, name="capital-project-table"),
    path("capital-project-add/", views.capital_project_add, name="capital-project-add"),
    path("capital-project-update/<int:pk>", views.capital_project_update, name="capital-project-update"),
    path("capital-project-delete/<int:pk>", views.capital_project_delete, name="capital-project-delete"),
    path("capital-project-upload", views.capital_project_upload, name="capital-project-upload"),
    path(
        "capital-forecasting-new-year-upload",
        views.capital_forecasting_new_year_upload,
        name="capital-forecasting-new-year-upload",
    ),
    path(
        "capital-forecasting-in-year-upload",
        views.capital_forecasting_in_year_upload,
        name="capital-forecasting-in-year-upload",
    ),
    path(
        "capital-forecasting-year-end-upload",
        views.capital_forecasting_year_end_upload,
        name="capital-forecasting-year-end-upload",
    ),
]
