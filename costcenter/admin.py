from django.contrib import admin

from costcenter.models import Fund, CostCenter, Source, FundCenter


class CostCenterAdmin(admin.ModelAdmin):
    list_display = ("costcenter", "parent", "fund", "source", "shortname", "isforecastable", "isupdatable")


class FundCenterAdmin(admin.ModelAdmin):
    list_display = ("fundcenter", "parent", "shortname")


class FundAdmin(admin.ModelAdmin):
    list_display = ("fund", "vote", "name")


admin.site.register(Fund, FundAdmin)
admin.site.register(CostCenter, CostCenterAdmin)
admin.site.register(Source)
admin.site.register(FundCenter, FundCenterAdmin)
