from django.contrib import admin

from .models import AuditLog, CurrencyRate, Dzo, Notification, UserProfile


@admin.register(Dzo)
class DzoAdmin(admin.ModelAdmin):
    list_display = ["code", "name_ru", "is_active"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "position", "department", "dzo"]
    filter_horizontal = ["allowed_dzos"]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "user", "object_type", "object_id", "action", "from_status", "to_status"]
    list_filter = ["object_type", "action"]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CurrencyRate)
class CurrencyRateAdmin(admin.ModelAdmin):
    list_display = ["date", "currency", "rate"]


admin.site.register(Notification)
