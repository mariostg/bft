from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.lineitem_page, name="lineitems"),
    path("lineitem/", views.lineitem_page, name="lineitems"),
    # path("lineitem/delete/<int:pk>", views.delete_line_item, name="delete-line-item"),
    # re_path(
    #     r"^costcenter/(?P<costcenter>[0-9]{4}[a-zA-Z]{2})/$", views.costcenter_lineitems, name="costcenter-lineitems"
    # ),
    # path("line_forecast/update/<int:pk>", views.update_line_forecast, name="update-line-forecast"),
    # path("line_forecast/wp/<int:pk>", views.update_line_forecast_to_wp, name="update-line-forecast-to-wp"),
    # path("line_forecast/zero/<int:pk>", views.update_line_forecast_zero, name="update-line-forecast-zero"),
    path("line-forecast/add/<int:pk>", views.line_forecast_add, name="line-forecast-add"),
    # path("line_forecast/delete/<int:pk>", views.delete_line_forecast, name="delete-line-forecast"),
    # path("line_forecasts", views.line_forecasts, name="line-forecasts"),
    # path(
    #     "costcenter/<str:costcenter>/",
    #     views.costcenter_lineitems,
    #     name="costcenter-linesitems",
    # ),
]
