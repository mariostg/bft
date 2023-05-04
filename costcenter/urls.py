from django.urls import path
from . import views

urlpatterns = [
    path("fund_page/", views.fund_page, name="fund-page"),
    path("new/", views.fund_new, name="fund-new"),
]
