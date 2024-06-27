from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("bft.urls")),
    path("bft/", include("bft.urls")),
    path("htmldocs/", include("htmldocs.urls")),
    path("reports/", include("reports.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
    path("__debug__/", include("debug_toolbar.urls")),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
