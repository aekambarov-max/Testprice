from django.conf import settings
from django.db import models


class Dzo(models.Model):
    """Справочник ДЗО Группы компаний АО НК «КазМунайГаз»."""

    code = models.CharField("Код", max_length=16, unique=True)
    name_ru = models.CharField("Наименование (рус.)", max_length=255)
    name_kk = models.CharField("Наименование (каз.)", max_length=255, blank=True)
    is_active = models.BooleanField("Активно", default=True)

    class Meta:
        verbose_name = "ДЗО"
        verbose_name_plural = "ДЗО"
        ordering = ["name_ru"]

    def __str__(self):
        return self.name_ru


class UserProfile(models.Model):
    """Дополнительные атрибуты сотрудника (в проде синхронизируются из LDAP/AD)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    position = models.CharField("Должность", max_length=255, blank=True)
    department = models.CharField("Подразделение", max_length=255, blank=True)
    dzo = models.ForeignKey(Dzo, verbose_name="ДЗО", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    allowed_dzos = models.ManyToManyField(Dzo, verbose_name="Доступные ДЗО", blank=True, related_name="+")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return full_name(self.user)


def full_name(user):
    if user is None:
        return ""
    profile = getattr(user, "profile", None)
    parts = [user.last_name, user.first_name, profile.middle_name if profile else ""]
    name = " ".join(p for p in parts if p)
    return name or user.get_username()


class AuditLog(models.Model):
    """Журнал аудита: переходы статусов, операции с КП и позициями, скачивания документов."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    object_type = models.CharField(max_length=64)
    object_id = models.CharField(max_length=64)
    action = models.CharField(max_length=64)
    from_status = models.CharField(max_length=32, blank=True)
    to_status = models.CharField(max_length=32, blank=True)
    comment = models.TextField(blank=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Запись журнала аудита"
        verbose_name_plural = "Журнал аудита"
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["object_type", "object_id"])]


class Notification(models.Model):
    """Уведомление в системе (колокольчик)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    event = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "is_read"])]


class NumberSequence(models.Model):
    """Счётчик для генератора номеров документов вида ID2026.EMG.0001."""

    prefix = models.CharField(max_length=16)
    year = models.PositiveIntegerField()
    dzo_code = models.CharField(max_length=16)
    last_value = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["prefix", "year", "dzo_code"], name="uniq_number_sequence")]


class CurrencyRate(models.Model):
    """Официальные курсы валют НБ РК (тенге за 1 единицу валюты)."""

    date = models.DateField()
    currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=14, decimal_places=4)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["date", "currency"], name="uniq_currency_rate")]
        ordering = ["-date", "currency"]
