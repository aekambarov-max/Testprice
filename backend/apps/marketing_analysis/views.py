from urllib.parse import quote

from django.conf import settings
from django.db.models import Count, OuterRef, Q, Subquery
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.core import roles
from apps.core.exceptions import BusinessError
from apps.core.models import AuditLog
from apps.core.services import audit, translit

from . import access, services, workflow
from .models import ON_APPROVAL_STATUSES, ApprovalStep, MarketingAnalysisItem, PdfStatus, Status
from .serializers import (
    AnalysisDetailSerializer,
    AnalysisListSerializer,
    AttachmentSerializer,
    HistoryAuditSerializer,
    ItemSerializer,
    OfferSerializer,
    StepSerializer,
)

TAB_FILTERS = {
    "draft": Q(status=Status.DRAFT),
    "collecting_kp": Q(status=Status.COLLECTING_KP),
    "on_approval": Q(status__in=ON_APPROVAL_STATUSES),
    "rework": Q(status=Status.REWORK),
    "approved": Q(status=Status.APPROVED),
    "cancelled": Q(status=Status.CANCELLED),
    "all": Q(),
}


class FeatureEnabled(permissions.BasePermission):
    def has_permission(self, request, view):
        if not settings.MA_ENABLED:
            raise Http404()
        return True


def _file_response(file_field, filename):
    if not file_field:
        raise Http404()
    response = FileResponse(file_field.open("rb"), as_attachment=True)
    ascii_name = translit(filename).encode("ascii", "ignore").decode() or "document"
    response["Content-Disposition"] = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(filename)}"
    return response


class MarketingAnalysisViewSet(viewsets.ViewSet):
    """/api/marketing-analyses/ — реестр, карточка и действия маршрута согласования."""

    permission_classes = [permissions.IsAuthenticated, FeatureEnabled]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    # --- helpers ---
    def _queryset(self):
        return access.visible_analyses(self.request.user)

    def _get(self, pk):
        return get_object_or_404(self._queryset(), pk=pk)

    def _detail(self, analysis_id, status_code=status.HTTP_200_OK):
        analysis = get_object_or_404(
            self._queryset().select_related("dzo", "author__profile", "initiator_user__profile")
            .prefetch_related("offers__prices", "approvers__user__profile"),
            pk=analysis_id,
        )
        return Response(AnalysisDetailSerializer(analysis, context={"request": self.request}).data,
                        status=status_code)

    def _awaiting_me(self, qs):
        user = self.request.user
        pending = ApprovalStep.objects.filter(analysis=OuterRef("pk"), iteration=OuterRef("iteration"),
                                              status=ApprovalStep.StepStatus.PENDING)
        my_roles = list(roles.user_roles(user))
        mine = pending.filter(Q(assignee_user=user) | Q(assignee_user__isnull=True, assignee_role__in=my_roles))
        return qs.filter(status__in=ON_APPROVAL_STATUSES, pk__in=Subquery(mine.values("analysis_id")))

    def _filtered(self, params):
        qs = self._queryset()
        if params.get("dzo"):
            qs = qs.filter(dzo_id=params["dzo"])
        if params.get("author"):
            qs = qs.filter(author_id=params["author"])
        if params.get("date_from"):
            qs = qs.filter(created_at__date__gte=params["date_from"])
        if params.get("date_to"):
            qs = qs.filter(created_at__date__lte=params["date_to"])
        if params.get("nsi_code"):
            qs = qs.filter(items__nsi_code__startswith=params["nsi_code"]).distinct()
        if params.get("q"):
            q = params["q"].strip()
            qs = qs.filter(Q(number__icontains=q) | Q(items__name__icontains=q) | Q(items__nsi_code__startswith=q)
                           ).distinct()
        return qs

    # --- registry ---
    def list(self, request):
        params = request.query_params
        base = self._filtered(params)
        counts = {key: base.filter(cond).count() for key, cond in TAB_FILTERS.items()}
        counts["awaiting_me"] = self._awaiting_me(base).count()

        tab = params.get("tab", "all")
        if tab == "awaiting_me" or params.get("awaiting_me") in ("1", "true"):
            qs = self._awaiting_me(base)
        else:
            qs = base.filter(TAB_FILTERS.get(tab, Q()))
        if params.get("status"):
            qs = qs.filter(status__in=params["status"].split(","))
        first_item = MarketingAnalysisItem.objects.filter(analysis=OuterRef("pk")).order_by("line_no")
        qs = (qs.select_related("dzo", "author__profile", "initiator_user__profile")
              .annotate(items_count=Count("items", distinct=True),
                        first_item_name=Subquery(first_item.values("name")[:1]))
              .order_by("-created_at", "-id"))

        from apps.core.pagination import StandardPagination

        paginator = StandardPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        response = paginator.get_paginated_response(AnalysisListSerializer(page, many=True).data)
        response.data["counts"] = counts
        return response

    def create(self, request):
        analysis = services.create_analysis(user=request.user, data=request.data, request=request)
        return self._detail(analysis.pk, status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        return self._detail(pk)

    def partial_update(self, request, pk=None):
        analysis = self._get(pk)
        services.update_analysis(analysis.pk, user=request.user, data=request.data, request=request)
        return self._detail(analysis.pk)

    def destroy(self, request, pk=None):
        analysis = self._get(pk)
        services.delete_draft(analysis.pk, user=request.user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --- items ---
    @action(detail=True, methods=["post"], url_path="items")
    def add_item(self, request, pk=None):
        analysis = self._get(pk)
        item = services.add_item(analysis.pk, user=request.user, data=request.data, request=request)
        return Response(ItemSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch", "delete"], url_path=r"items/(?P<item_id>\d+)")
    def item(self, request, pk=None, item_id=None):
        analysis = self._get(pk)
        get_object_or_404(analysis.items, pk=item_id)
        if request.method == "DELETE":
            services.delete_item(analysis.pk, int(item_id), user=request.user, request=request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        item = services.update_item(analysis.pk, int(item_id), user=request.user, data=request.data, request=request)
        return Response(ItemSerializer(item).data)

    @action(detail=True, methods=["post"], url_path=r"items/(?P<item_id>\d+)/attachments")
    def add_attachment(self, request, pk=None, item_id=None):
        analysis = self._get(pk)
        get_object_or_404(analysis.items, pk=item_id)
        att = services.add_attachment(analysis.pk, int(item_id), user=request.user, upload=request.FILES.get("file"),
                                      request=request)
        return Response(AttachmentSerializer(att).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "delete"], url_path=r"items/(?P<item_id>\d+)/attachments/(?P<att_id>\d+)")
    def attachment(self, request, pk=None, item_id=None, att_id=None):
        analysis = self._get(pk)
        item = get_object_or_404(analysis.items, pk=item_id)
        att = get_object_or_404(item.attachments, pk=att_id)
        if request.method == "DELETE":
            services.delete_attachment(analysis.pk, item.pk, att.pk, user=request.user, request=request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return _file_response(att.file, att.original_name)

    # --- offers ---
    @action(detail=True, methods=["post"], url_path="offers")
    def add_offer(self, request, pk=None):
        analysis = self._get(pk)
        offer = services.add_offer(analysis.pk, user=request.user, data=request.data,
                                   upload=request.FILES.get("file"), request=request)
        return Response(OfferSerializer(offer).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "delete"], url_path=r"offers/(?P<offer_id>\d+)")
    def offer(self, request, pk=None, offer_id=None):
        analysis = self._get(pk)
        offer = get_object_or_404(analysis.offers, pk=offer_id)
        if request.method == "DELETE":
            services.delete_offer(analysis.pk, offer.pk, user=request.user, request=request)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return _file_response(offer.file, offer.original_name)

    @action(detail=True, methods=["post"], url_path="request-kp")
    def request_kp(self, request, pk=None):
        analysis = self._get(pk)
        sent = services.request_kp(analysis.pk, user=request.user, supplier_ids=request.data.get("suppliers"),
                                   message=request.data.get("message", ""), request=request)
        return Response({"sent": len(sent)})

    @action(detail=True, methods=["post"], url_path="start-collecting")
    def start_collecting(self, request, pk=None):
        analysis = self._get(pk)
        workflow.start_collecting(analysis.pk, user=request.user, request=request)
        return self._detail(analysis.pk)

    @action(detail=True, methods=["post"])
    def calculate(self, request, pk=None):
        analysis = self._get(pk)
        services.calculate(analysis.pk, user=request.user, request=request)
        return self._detail(analysis.pk)

    @action(detail=True, methods=["get"])
    def analytics(self, request, pk=None):
        return Response(services.analytics(self._get(pk)))

    # --- route ---
    @action(detail=True, methods=["put"])
    def approvers(self, request, pk=None):
        analysis = self._get(pk)
        user_ids = request.data.get("approvers") if isinstance(request.data, dict) else request.data
        services.set_approvers(analysis.pk, user=request.user, user_ids=user_ids, request=request)
        return self._detail(analysis.pk)

    @action(detail=True, methods=["get"], url_path="submit-check")
    def submit_check(self, request, pk=None):
        return Response({"errors": workflow.validate_for_submit(self._get(pk))})

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        analysis = self._get(pk)
        workflow.submit(analysis.pk, user=request.user, request=request)
        return self._detail(analysis.pk)

    @action(detail=True, methods=["post"])
    def decision(self, request, pk=None):
        analysis = self._get(pk)
        workflow.decide(analysis.pk, user=request.user, decision=request.data.get("decision"),
                        comment=request.data.get("comment", ""), step_id=request.data.get("step_id"),
                        request=request)
        return self._detail(analysis.pk)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        analysis = self._get(pk)
        workflow.cancel(analysis.pk, user=request.user, comment=request.data.get("comment", ""), request=request)
        return self._detail(analysis.pk)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        analysis = self._get(pk)
        steps = analysis.steps.select_related("assignee_user__profile").order_by("iteration", "stage", "order")
        events = AuditLog.objects.filter(object_type=analysis._meta.label_lower, object_id=str(analysis.pk)
                                         ).select_related("user__profile").order_by("created_at", "id")
        return Response({"steps": StepSerializer(steps, many=True).data,
                         "events": HistoryAuditSerializer(events, many=True).data})

    @action(detail=True, methods=["get"], url_path="conclusion.pdf")
    def conclusion(self, request, pk=None):
        analysis = self._get(pk)
        if analysis.status != Status.APPROVED:
            raise BusinessError("not_approved", "Заключение доступно только для утверждённого анализа",
                                status_code=status.HTTP_404_NOT_FOUND)
        if analysis.pdf_status != PdfStatus.READY or not analysis.pdf_file:
            return Response({"code": "pdf_pending", "detail": "Заключение формируется…",
                             "pdf_status": analysis.pdf_status}, status=status.HTTP_409_CONFLICT)
        audit(analysis, "pdf_downloaded", request=request, payload={"sha256": analysis.pdf_sha256})
        response = _file_response(analysis.pdf_file, f"Маркетинговое_заключение_{analysis.number}.pdf")
        response["Content-Type"] = "application/pdf"
        response["X-Content-SHA256"] = analysis.pdf_sha256
        return response
