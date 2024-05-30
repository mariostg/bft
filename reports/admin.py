from django.contrib import admin

from reports.models import (
    CostCenterMonthlyEncumbrance,
    CostCenterMonthlyForecastAdjustment,
    CostCenterMonthlyLineItemForecast,
    CostCenterMonthlyAllocation,
)


class CostCenterMonthlyAllocationAdmin(admin.ModelAdmin):
    list_display = (
        "costcenter",
        "fund",
        "fy",
        "period",
        "allocation",
    )


class CostCenterMonthlyForecastLineItemAdmin(admin.ModelAdmin):
    list_display = (
        "costcenter",
        "fund",
        "fy",
        "period",
        "line_item_forecast",
    )


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


admin.site.register(CostCenterMonthlyAllocation, CostCenterMonthlyAllocationAdmin)

admin.site.register(CostCenterMonthlyEncumbrance, CostCenterMonthlyAdmin)

admin.site.register(CostCenterMonthlyLineItemForecast, CostCenterMonthlyForecastLineItemAdmin)

admin.site.register(CostCenterMonthlyForecastAdjustment, CostCenterMonthlyForecastAdjustmentAdmin)
