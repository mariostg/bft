from django.urls import path, re_path

from .views import serve_docs


urlpatterns = [
    re_path(r"^(?P<path>.*)$", serve_docs),
]
