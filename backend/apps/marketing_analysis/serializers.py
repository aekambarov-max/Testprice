from rest_framework import serializers

from apps.core import roles
from apps.core.models import AuditLog, full_name
from apps.core.serializers import DzoSerializer, UserShortSerializer

from . import access
from .models import (
    AnalysisApprover,
    ApprovalStep,
    CommercialOffer,
    CommercialOfferPrice,
    ItemAttachment,
    MarketingAnalysis,
    MarketingAnalysisItem,
    Stage,
)


def step_assignee_display(step):
    if step.assignee_user_id:
        return full_name(step.assignee_user)
    return roles.ROLE_TITLES.get(step.assignee_role, step.assignee_role)


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemAttachment
        fields = ["id", "original_name", "uploaded_at"]


class ItemSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)
    offers_count = serializers.SerializerMethodField()

    class Meta:
        model = MarketingAnalysisItem
        fields = ["id", "line_no", "nsi_product", "nsi_code", "enstru_code", "name", "characteristics", "unit",
                  "quantity", "delivery_place", "delivery_term", "marketing_price", "total_wo_vat", "calc_method",
                  "price_justification", "attachments", "offers_count"]

    def get_offers_count(self, obj):
        return len(obj.offer_prices.all())


class OfferPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommercialOfferPrice
        fields = ["item", "price", "price_kzt_wo_vat"]


class OfferSerializer(serializers.ModelSerializer):
    prices = OfferPriceSerializer(many=True, read_only=True)

    class Meta:
        model = CommercialOffer
        fields = ["id", "supplier", "supplier_name", "supplier_bin", "offer_date", "currency", "exchange_rate",
                  "vat_included", "original_name", "source", "created_at", "prices"]


class ApproverSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = AnalysisApprover
        fields = ["order", "user"]


class StepSerializer(serializers.ModelSerializer):
    stage_display = serializers.CharField(source="get_stage_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    assignee = serializers.SerializerMethodField()

    class Meta:
        model = ApprovalStep
        fields = ["id", "iteration", "stage", "stage_display", "order", "assignee", "assignee_role", "status",
                  "status_display", "decided_by_name", "decided_by_position", "comment", "activated_at",
                  "decided_at"]

    def get_assignee(self, obj):
        return step_assignee_display(obj)


class AnalysisListSerializer(serializers.ModelSerializer):
    dzo = DzoSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    author_name = serializers.SerializerMethodField()
    initiator = serializers.CharField(source="initiator_display", read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    first_item_name = serializers.CharField(read_only=True)

    class Meta:
        model = MarketingAnalysis
        fields = ["id", "number", "status", "status_display", "dzo", "author_name", "initiator", "created_at",
                  "submitted_at", "approved_at", "total_wo_vat", "items_count", "first_item_name", "current_stage"]

    def get_author_name(self, obj):
        return full_name(obj.author)


class AnalysisDetailSerializer(AnalysisListSerializer):
    initiator_user = UserShortSerializer(read_only=True)
    items = serializers.SerializerMethodField()
    offers = OfferSerializer(many=True, read_only=True)
    approvers = ApproverSerializer(many=True, read_only=True)
    route = serializers.SerializerMethodField()
    current_step_id = serializers.SerializerMethodField()
    available_actions = serializers.SerializerMethodField()
    fixed_stages = serializers.SerializerMethodField()
    pdf_name = serializers.SerializerMethodField()

    class Meta(AnalysisListSerializer.Meta):
        fields = AnalysisListSerializer.Meta.fields + [
            "initiator_user", "initiator_full_name", "initiator_position", "initiator_department",
            "price_justification", "iteration", "returned_from_stage", "cancelled_at", "updated_at",
            "items", "offers", "approvers", "route", "current_step_id", "available_actions", "fixed_stages",
            "pdf_status", "pdf_sha256", "pdf_generated_at", "pdf_name",
        ]

    def _current_step(self, obj):
        if not hasattr(obj, "_current_step_cache"):
            obj._current_step_cache = access.current_step(obj)
        return obj._current_step_cache

    def get_items(self, obj):
        return ItemSerializer(obj.items.prefetch_related("attachments", "offer_prices"), many=True).data

    def get_route(self, obj):
        steps = obj.steps.filter(iteration=obj.iteration).select_related("assignee_user") if obj.iteration else []
        return StepSerializer(steps, many=True).data

    def get_current_step_id(self, obj):
        step = self._current_step(obj)
        return step.pk if step else None

    def get_available_actions(self, obj):
        return access.available_actions(self.context["request"].user, obj, self._current_step(obj))

    def get_fixed_stages(self, obj):
        return [
            {"stage": Stage.DB, "title": Stage.DB.label, "assignee": roles.ROLE_TITLES[roles.DB_SPECIALIST]},
            {"stage": Stage.DIRECTOR, "title": Stage.DIRECTOR.label, "assignee": roles.ROLE_TITLES[roles.DB_DIRECTOR]},
        ]

    def get_pdf_name(self, obj):
        return f"Маркетинговое_заключение_{obj.number}.pdf"


class HistoryAuditSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ["id", "created_at", "user_name", "action", "from_status", "to_status", "comment"]

    def get_user_name(self, obj):
        return full_name(obj.user) if obj.user else "Система"
