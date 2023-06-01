from django.contrib import admin
from . import models


class LineItemAdmin(admin.ModelAdmin):
    list_display = [
        "docno",
        "lineno",
        "doctype",
        "enctype",
        "fund",
        "costcenter",
        "fundcenter",
        "status",
        "fcintegrity",
        "spent",
        "balance",
        "workingplan",
        "linetext",
    ]


# Register your models here.
admin.site.register(models.LineItem, LineItemAdmin)
