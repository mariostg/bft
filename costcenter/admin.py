from django.contrib import admin

from costcenter.models import Fund, CostCenter, Source, FundCenter

admin.site.register(Fund)
admin.site.register(CostCenter)
admin.site.register(Source)
admin.site.register(FundCenter)
