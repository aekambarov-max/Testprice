from django.contrib import admin

from .models import AnalysisApprover, ApprovalStep, CommercialOffer, MarketingAnalysis, MarketingAnalysisItem


class ItemInline(admin.TabularInline):
    model = MarketingAnalysisItem
    extra = 0
    can_delete = False
    readonly_fields = ["line_no", "nsi_code", "name", "unit", "quantity", "marketing_price", "total_wo_vat"]
    fields = readonly_fields


class StepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    can_delete = False
    readonly_fields = ["iteration", "stage", "order", "assignee_user", "assignee_role", "status", "decided_by_name",
                       "decided_at", "comment"]
    fields = readonly_fields


@admin.register(MarketingAnalysis)
class MarketingAnalysisAdmin(admin.ModelAdmin):
    """Только просмотр: изменение статусов допускается исключительно через state machine (API)."""

    list_display = ["number", "dzo", "status", "author", "created_at", "approved_at", "pdf_status"]
    list_filter = ["status", "dzo", "pdf_status"]
    search_fields = ["number"]
    inlines = [ItemInline, StepInline]

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(CommercialOffer)
admin.site.register(AnalysisApprover)
