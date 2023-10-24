from django.contrib import admin

from .models import CostCenterChargeImport


class CostCenterChargeImportAdmin(admin.ModelAdmin):
    list_display = ["fund", "costcenter", "ref_doc_no", "doc_type", "amount", "posting_date", "period"]


admin.site.register(CostCenterChargeImport, CostCenterChargeImportAdmin)
