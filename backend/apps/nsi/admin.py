from django.contrib import admin

from .models import NsiProduct


@admin.register(NsiProduct)
class NsiProductAdmin(admin.ModelAdmin):
    list_display = ["nsi_code", "enstru_code", "name", "unit", "is_active"]
    search_fields = ["nsi_code", "name", "enstru_code"]
