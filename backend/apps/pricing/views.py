from rest_framework import generics, serializers

from .models import PriceCatalogEntry


class PriceCatalogEntrySerializer(serializers.ModelSerializer):
    dzo = serializers.CharField(source="dzo.name_ru")

    class Meta:
        model = PriceCatalogEntry
        fields = ["id", "nsi_code", "enstru_code", "name", "unit", "dzo", "price_wo_vat", "approved_at",
                  "source_type", "source_id", "source_number", "is_active"]


class PriceCatalogListView(generics.ListAPIView):
    """GET /api/price-catalog/?q= — каталог цен (действующие исследования)."""

    serializer_class = PriceCatalogEntrySerializer

    def get_queryset(self):
        qs = PriceCatalogEntry.objects.select_related("dzo").filter(is_active=True)
        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(nsi_code__startswith=q) | qs.filter(name__icontains=q)
        return qs
