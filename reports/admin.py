from django.contrib import admin

from reports.models import CostCenterMonthlyEncumbrance


class CostCenterMonthlyAdmin(admin.ModelAdmin):
    list_display = (
        "costcenter",
        "fund",
        "fy",
        "period",
        "spent",
        "commitment",
        "pre_commitment",
        "fund_reservation",
        "balance",
        "working_plan",
        "spent",
    )


admin.site.register(CostCenterMonthlyEncumbrance, CostCenterMonthlyAdmin)
