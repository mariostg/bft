from django.urls import path
from . import views

urlpatterns = [
    path("", views.line_items, name="lineitem-report"),
    path("bmt-screening/", views.bmt_screening_report, name="bmt-screening-report"),
    path("allocation-status/", views.allocation_status_report, name="allocation-status-report"),
    path(
        "allocation-status/<str:fundcenter>/<str:fund>/<int:fy>/<int:quarter>/",
        views.allocation_status_report,
        name="allocation-status-report",
    ),
    path("financial-structure/", views.financial_structure_report, name="financial-structure-report"),
    path("lineitems/", views.line_items, name="lineitem-report"),
    path("lineitems-csv/", views.csv_line_items, name="lineitem-csv"),
    path("costcenter-monthly-data/", views.costcenter_monthly_data, name="costcenter-monthly-data"),
    path(
        "charges/<str:cc>/<int:fy>/<int:period>/", views.cost_center_charge_table, name="costcenter-charges"
    ),
    path("capital-forecasting-table", views.capital_forecasting_table, name="capital-forecasting-table"),
]
