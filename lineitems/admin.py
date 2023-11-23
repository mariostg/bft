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


class LineForecastAdmin(admin.ModelAdmin):
    list_display = (
        "forecastamount",
        "spent_initial",
        "balance_initial",
        "workingplan_initial",
        "description",
        "comment",
        "deliverydate",
        "delivered",
        "lineitem",
        "buyer",
        "updated",
        "created",
        "status",
        "owner",
    )


# Register your models here.
admin.site.register(models.LineItem, LineItemAdmin)
admin.site.register(models.LineForecast, LineForecastAdmin)
