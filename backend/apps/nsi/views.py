from django.db.models import Q
from rest_framework import generics, serializers

from .models import NsiProduct


class NsiProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = NsiProduct
        fields = ["id", "nsi_code", "enstru_code", "name", "short_description", "unit"]


class NsiProductSearchView(generics.ListAPIView):
    """GET /api/nsi/products/?q= — поиск по коду АСУ НСИ или наименованию."""

    serializer_class = NsiProductSerializer
    pagination_class = None

    def get_queryset(self):
        q = (self.request.query_params.get("q") or "").strip()
        qs = NsiProduct.objects.filter(is_active=True)
        if q:
            qs = qs.filter(Q(nsi_code__istartswith=q) | Q(name__icontains=q) | Q(enstru_code__istartswith=q))
        return qs[:20]
