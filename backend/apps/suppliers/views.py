from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import KpRequest, Supplier
from .services import get_response_handler


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "bin", "name", "email"]


class SupplierListView(generics.ListAPIView):
    """GET /api/suppliers/?q= — пул поставщиков."""

    serializer_class = SupplierSerializer
    pagination_class = None

    def get_queryset(self):
        q = (self.request.query_params.get("q") or "").strip()
        qs = Supplier.objects.filter(is_active=True)
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(bin__startswith=q))
        return qs[:50]


class KpResponseView(APIView):
    """Публичная ссылка для поставщика: GET — что запрошено, POST — подать КП (файл + цены)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, token):
        req = get_object_or_404(KpRequest.objects.select_related("supplier"), token=token)
        return Response(
            {"supplier": req.supplier.name, "items": req.items, "status": req.status, "message": req.message}
        )

    def post(self, request, token):
        req = get_object_or_404(KpRequest.objects.select_related("supplier"), token=token)
        handler = get_response_handler(req.source_type)
        if handler is None:
            return Response({"code": "not_supported", "detail": "Источник запроса не принимает ответы"}, status=400)
        return handler(request, req)
