from django.contrib import admin

from costcenter.models import (
    Fund,
    CostCenter,
    Source,
    FundCenter,
    CostCenterAllocation,
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
    list_display = ("fundcenter", "fundcenter_parent", "shortname", "sequence")


class FundAdmin(admin.ModelAdmin):
    list_display = ("fund", "vote", "name")


class CostCenterAllocationAdmin(admin.ModelAdmin):
    list_display = ("costcenter", "fund", "fy", "quarter", "amount", "owner", "note")


admin.site.register(Fund, FundAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Source)
admin.site.register(FundCenter, FundCenterAdmin)
admin.site.register(CostCenterAllocation, CostCenterAllocationAdmin)
