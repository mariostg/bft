from django.contrib import admin

from reports.models import (CostCenterMonthlyAllocation,
                            CostCenterMonthlyEncumbrance,
                            CostCenterMonthlyForecastAdjustment,
                            CostCenterMonthlyLineItemForecast)


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


class CostCenterMonthlyEncumbranceAdmin(admin.ModelAdmin):
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
    )


admin.site.register(CostCenterMonthlyAllocation, CostCenterMonthlyAllocationAdmin)

admin.site.register(CostCenterMonthlyEncumbrance, CostCenterMonthlyEncumbranceAdmin)

admin.site.register(CostCenterMonthlyLineItemForecast, CostCenterMonthlyForecastLineItemAdmin)

admin.site.register(CostCenterMonthlyForecastAdjustment, CostCenterMonthlyForecastAdjustmentAdmin)
