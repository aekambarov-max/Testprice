from django.contrib import admin

from .models import KpRequest, Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "bin", "email", "is_active"]
    search_fields = ["name", "bin"]


@admin.register(KpRequest)
class KpRequestAdmin(admin.ModelAdmin):
    list_display = ["supplier", "source_type", "source_id", "status", "sent_at"]
