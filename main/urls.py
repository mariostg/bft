from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("bft.urls")),
    path("bft/", include("bft.urls")),
    # path("fund/", include("costcenter.urls")),
    # path("source/", include("costcenter.urls")),
    # path("fundcenter/", include("costcenter.urls")),
    # path("costcenter/", include("costcenter.urls")),
    # path("lineitem/", include("lineitems.urls")),
    path("reports/", include("reports.urls")),
    # path("charges/", include("charges.urls")),
    # path("users/", include("users.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
