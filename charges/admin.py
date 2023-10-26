from django.contrib import admin

from .models import CostCenterChargeMonthly, CostCenterChargeImport


class CostCenterChargeImportAdmin(admin.ModelAdmin):
    list_display = ["fund", "costcenter", "ref_doc_no", "doc_type", "amount", "posting_date", "period", "fy"]


class CostCenterChargeMonthlyAdmin(admin.ModelAdmin):
    list_display = ["fund", "costcenter", "amount", "fy", "period"]


admin.site.register(CostCenterChargeImport, CostCenterChargeImportAdmin)
admin.site.register(CostCenterChargeMonthly, CostCenterChargeMonthlyAdmin)
