from django.contrib import admin

# from django.contrib.auth.admin import UserAdmin
from users.models import BftUser


class BftUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "default_fc",
        "default_cc",
        "email",
        "last_login",
        "date_joined",
        "is_active",
        "procurement_officer",
    )


admin.site.register(BftUser, BftUserAdmin)
