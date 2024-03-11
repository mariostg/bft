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
]
urlpatterns += [
    path(
        "capital-forecasting-estimates",
        views.capital_forecasting_estimates,
        name="capital-forecasting-estimates",
    ),
    path(
        "capital-forecasting-quarterly",
        views.capital_forecasting_quarterly,
        name="capital-forecasting-quarterly",
    ),
    path(
        "capital-historical-outlook",
        views.capital_historical_outlook,
        name="capital-historical-outlook",
    ),
    path(
        "capital-forecasting-fears",
        views.capital_forecasting_fears,
        name="capital-forecasting-fears",
    ),
    path(
        "capital-forecasting-dashboard",
        views.capital_forecasting_dashboard,
        name="capital-forecasting-dashboard",
    ),
]
