from django.db import models

from apps.core.models import Dzo


class PriceCatalogEntry(models.Model):
    """Каталог цен: действующие маркетинговые исследования по позициям АСУ НСИ."""

    nsi_code = models.CharField("Код АСУ НСИ", max_length=32, db_index=True)
    enstru_code = models.CharField("Код ЕНС ТРУ", max_length=64, blank=True)
    name = models.CharField("Наименование", max_length=500)
    unit = models.CharField("Ед. изм.", max_length=32)
    dzo = models.ForeignKey(Dzo, on_delete=models.PROTECT, related_name="+")
    price_wo_vat = models.DecimalField("Маркетинговая цена за ед. без НДС, KZT", max_digits=18, decimal_places=2)
    approved_at = models.DateTimeField("Дата утверждения")
    source_type = models.CharField(max_length=64)
    source_id = models.CharField(max_length=64)
    source_number = models.CharField("Номер документа-основания", max_length=64)
    is_active = models.BooleanField("Действующее", default=True)

    class Meta:
        verbose_name = "Позиция каталога цен"
        verbose_name_plural = "Каталог цен"
        ordering = ["-approved_at", "-id"]
        indexes = [models.Index(fields=["nsi_code", "is_active"])]
