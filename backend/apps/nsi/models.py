from django.db import models


class NsiProduct(models.Model):
    """Материал/товар из АСУ НСИ (в проде загружается из АСУ НСИ через SAP PI/PO, связан с кодом ЕНС ТРУ)."""

    nsi_code = models.CharField("Код АСУ НСИ", max_length=32, unique=True)
    enstru_code = models.CharField("Код ЕНС ТРУ", max_length=64, blank=True)
    name = models.CharField("Наименование", max_length=500)
    short_description = models.TextField("Краткая характеристика", blank=True)
    unit = models.CharField("Единица измерения", max_length=32)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Товар АСУ НСИ"
        verbose_name_plural = "Товары АСУ НСИ"
        ordering = ["nsi_code"]

    def __str__(self):
        return f"{self.nsi_code} {self.name}"
