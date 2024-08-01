from django.contrib import admin

from bft.models import (BftUser, Bookmark, CapitalInYear, CapitalNewYear,
                        CapitalYearEnd, CostCenter, CostCenterAllocation,
                        CostCenterChargeImport, CostCenterChargeMonthly, Fund,
                        FundCenter, Source)

from . import models


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("owner", "bookmark_name", "bookmark_link")


class BftUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "default_fc",
        "default_cc",
        "email",
        "last_login",
        "date_joined",
        "is_active",
        "procurement_officer",
    )


class CostCenterAdmin(admin.ModelAdmin):
    list_display = (
        "costcenter",
        "costcenter_parent",
        "fund",
        "source",
        "shortname",
        "isforecastable",
        "isupdatable",
        "sequence",
    )


class FundCenterAdmin(admin.ModelAdmin):
    list_display = ("fundcenter", "fundcenter_parent", "shortname", "sequence", "level")


class FundAdmin(admin.ModelAdmin):
    list_display = ("fund", "vote", "name")


class CostCenterAllocationAdmin(admin.ModelAdmin):
    list_display = ("costcenter", "fund", "fy", "quarter", "amount", "owner", "note")


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
        "status",
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
        "owner",
    )


class LineItemImportAdmin(admin.ModelAdmin):
    list_display = (
        "docno",
        "lineno",
        "fund",
        "costcenter",
        "fundcenter",
        "doctype",
        "enctype",
        "spent",
        "balance",
        "workingplan",
        "linetext",
    )


class CostCenterChargeImportAdmin(admin.ModelAdmin):
    list_display = [
        "fund",
        "costcenter",
        "ref_doc_no",
        "doc_type",
        "amount",
        "posting_date",
        "period",
        "fy",
    ]


class CostCenterChargeMonthlyAdmin(admin.ModelAdmin):
    list_display = ["fund", "costcenter", "amount", "fy", "period"]


# Register your models here.'
admin.site.register(Bookmark)
admin.site.register(BftUser, BftUserAdmin)
admin.site.register(models.LineItem, LineItemAdmin)
admin.site.register(models.LineForecast, LineForecastAdmin)
admin.site.register(models.LineItemImport, LineItemImportAdmin)
admin.site.register(Fund, FundAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Source)
admin.site.register(CapitalYearEnd)
admin.site.register(CapitalInYear)
admin.site.register(CapitalNewYear)
admin.site.register(FundCenter, FundCenterAdmin)
admin.site.register(CostCenterAllocation, CostCenterAllocationAdmin)


admin.site.register(CostCenterChargeImport, CostCenterChargeImportAdmin)
admin.site.register(CostCenterChargeMonthly, CostCenterChargeMonthlyAdmin)
