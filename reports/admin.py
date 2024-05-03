from django.contrib import admin

from reports.models import CostCenterMonthlyEncumbrance, CostCenterMonthlyForecastAdjustment


class CostCenterMonthlyForecastAdjustmentAdmin(admin.ModelAdmin):
    list_display = (
        "costcenter",
        "fund",
        "fy",
        "period",
        "forecast_adjustment",
    )


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

admin.site.register(CostCenterMonthlyForecastAdjustment, CostCenterMonthlyForecastAdjustmentAdmin)
