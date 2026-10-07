from django.contrib import admin

from .models import PriceCatalogEntry


@admin.register(PriceCatalogEntry)
class PriceCatalogEntryAdmin(admin.ModelAdmin):
    list_display = ["nsi_code", "name", "dzo", "price_wo_vat", "approved_at", "source_number", "is_active"]
    search_fields = ["nsi_code", "name", "source_number"]
