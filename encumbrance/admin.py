from django.contrib import admin
from .models import EncumbranceImport


class EncumbranceAdmin(admin.ModelAdmin):
    list_display = (
        "docno",
        "lineno",
        "fund",
        "costcenter",
        "doctype",
        "enctype",
        "spent",
        "balance",
        "workingplan",
        "linetext",
    )


admin.site.register(EncumbranceImport, EncumbranceAdmin)
