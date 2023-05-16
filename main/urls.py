from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("fund/", include("costcenter.urls")),
    path("source/", include("costcenter.urls")),
]
