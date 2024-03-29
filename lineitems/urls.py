from django.urls import path, re_path
from . import views

urlpatterns = [
    path("", views.lineitem_page, name="lineitem-page"),
    path("lineitem/", views.lineitem_page, name="lineitem-page"),
    path("lineitem/delete/<int:pk>", views.line_item_delete, name="line-item-delete"),
    path("fundcenter-lineitem-upload", views.fundcenter_lineitem_upload, name="fundcenter-lineitem-upload"),
    path("costcenter-lineitem-upload", views.costcenter_lineitem_upload, name="costcenter-lineitem-upload"),
    path("line_forecast/update/<int:pk>", views.line_forecast_update, name="line-forecast-update"),
    path("line_forecast/wp/<int:pk>", views.line_forecast_to_wp_update, name="line-forecast-to-wp-update"),
    path("line_forecast/zero/<int:pk>", views.line_forecast_zero_update, name="line-forecast-zero-update"),
    path("line-forecast/add/<int:pk>", views.line_forecast_add, name="line-forecast-add"),
    path("line_forecast/delete/<int:pk>", views.line_forecast_delete, name="line-forecast-delete"),
    path("document-forecast/<str:docno>", views.document_forecast, name="document-forecast"),
    path("costcenter-forecast/<int:costcenter_pk>", views.costcenter_forecast, name="costcenter-forecast"),
]
