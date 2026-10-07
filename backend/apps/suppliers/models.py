import uuid

from django.conf import settings
from django.db import models


class Supplier(models.Model):
    """Пул поставщиков."""

    bin = models.CharField("БИН", max_length=12, unique=True)
    name = models.CharField("Наименование", max_length=500)
    email = models.EmailField("Email для запросов КП", blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Поставщик"
        verbose_name_plural = "Пул поставщиков"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.bin})"


class KpRequest(models.Model):
    """Запрос коммерческого предложения, направленный поставщику. Источник — любой документ системы."""

    class Status(models.TextChoices):
        SENT = "sent", "Отправлен"
        ANSWERED = "answered", "Получен ответ"

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="kp_requests")
    source_type = models.CharField(max_length=64)
    source_id = models.CharField(max_length=64)
    message = models.TextField(blank=True)
    items = models.JSONField(default=list)  # снимок запрошенных позиций
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SENT)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    sent_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-sent_at"]
        indexes = [models.Index(fields=["source_type", "source_id"])]
