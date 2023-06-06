from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("bft.urls")),
    path("bft/", include("bft.urls")),
    path("fund/", include("costcenter.urls")),
    path("source/", include("costcenter.urls")),
    path("fundcenter/", include("costcenter.urls")),
    path("costcenter/", include("costcenter.urls")),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
