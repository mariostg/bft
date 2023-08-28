from django.contrib import admin
from reports.models import CostCenterMonthly


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
        "allocation",
        "forecast",
        "spent",
    )


admin.site.register(CostCenterMonthly, CostCenterMonthlyAdmin)
