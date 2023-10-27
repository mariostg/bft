from django.urls import path
from . import views

urlpatterns = [
    path("", views.cost_center_charge_upload, name="cost-center-charges-upload"),
    path("cc_charge_upload", views.cost_center_charge_upload, name="cost-center-charges-upload"),
]
