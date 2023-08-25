from django.urls import path
from . import views

urlpatterns = [path("", views.HomeView.as_view(), name="bft")]

urlpatterns += [
    path("bft-status", views.bft_status, name="bft-status"),
    path("bft-fy-update", views.bft_fy_update, name="bft-fy-update"),
    path("bft-quarter-update", views.bft_quarter_update, name="bft-quarter-update"),
    path("bft-period-update", views.bft_period_update, name="bft-period-update"),
]
