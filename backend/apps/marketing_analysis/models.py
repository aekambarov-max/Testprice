from django.conf import settings
from django.db import models

from apps.core.models import Dzo
from apps.nsi.models import NsiProduct
from apps.suppliers.models import KpRequest, Supplier


class Status(models.TextChoices):
    DRAFT = "draft", "Черновик"
    COLLECTING_KP = "collecting_kp", "Сбор КП"
    ON_APPROVAL_DZO = "on_approval_dzo", "На согласовании (ДЗО)"
    ON_APPROVAL_DB = "on_approval_db", "На согласовании ДБ КМГ"
    ON_FINAL_APPROVAL = "on_final_approval", "На утверждении директора ДБ КМГ"
    REWORK = "rework", "На доработке"
    APPROVED = "approved", "Утверждено"
    CANCELLED = "cancelled", "Аннулировано"


EDITABLE_STATUSES = (Status.DRAFT, Status.COLLECTING_KP, Status.REWORK)
ON_APPROVAL_STATUSES = (Status.ON_APPROVAL_DZO, Status.ON_APPROVAL_DB, Status.ON_FINAL_APPROVAL)


class Stage(models.IntegerChoices):
    DZO = 1, "Согласующие ДЗО"
    DB = 2, "Департамент бюджетирования КМГ"
    DIRECTOR = 3, "Директор департамента бюджетирования КМГ"


STAGE_STATUS = {
    Stage.DZO: Status.ON_APPROVAL_DZO,
    Stage.DB: Status.ON_APPROVAL_DB,
    Stage.DIRECTOR: Status.ON_FINAL_APPROVAL,
}


class PdfStatus(models.TextChoices):
    NONE = "none", "Нет"
    PENDING = "pending", "Формируется"
    READY = "ready", "Готово"
    FAILED = "failed", "Ошибка"


def upload_offer_to(instance, filename):
    return f"marketing_analysis/{instance.analysis_id}/offers/{filename}"


def upload_attachment_to(instance, filename):
    return f"marketing_analysis/{instance.item.analysis_id}/items/{instance.item_id}/{filename}"


class MarketingAnalysis(models.Model):
    number = models.CharField("Номер", max_length=32, unique=True)
    dzo = models.ForeignKey(Dzo, verbose_name="ДЗО", on_delete=models.PROTECT, related_name="+")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Маркетолог", on_delete=models.PROTECT, related_name="+"
    )
    # Инициатор потребности: сотрудник из справочника или ФИО текстом (если нет в справочнике).
    initiator_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    initiator_full_name = models.CharField("Инициатор (ФИО)", max_length=255, blank=True)
    initiator_position = models.CharField("Должность инициатора", max_length=255, blank=True)
    initiator_department = models.CharField("Подразделение инициатора", max_length=255, blank=True)

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    current_stage = models.PositiveSmallIntegerField(null=True, blank=True, choices=Stage.choices)
    iteration = models.PositiveIntegerField("Итерация маршрута (счётчик отправок)", default=0)
    returned_from_stage = models.PositiveSmallIntegerField(null=True, blank=True, choices=Stage.choices)

    price_justification = models.TextField("Обоснование цены", blank=True)
    total_wo_vat = models.DecimalField("Итоговая сумма без НДС, KZT", max_digits=20, decimal_places=2, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    pdf_file = models.FileField(upload_to="marketing_analysis/conclusions/", blank=True)
    pdf_sha256 = models.CharField(max_length=64, blank=True)
    pdf_status = models.CharField(max_length=16, choices=PdfStatus.choices, default=PdfStatus.NONE)
    pdf_generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Маркетинговый анализ"
        verbose_name_plural = "Маркетинговые анализы"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["dzo", "status"]),
            models.Index(fields=["author"]),
        ]

    def __str__(self):
        return self.number

    @property
    def is_editable(self):
        return self.status in EDITABLE_STATUSES

    @property
    def initiator_display(self):
        from apps.core.models import full_name

        return full_name(self.initiator_user) if self.initiator_user else self.initiator_full_name


class MarketingAnalysisItem(models.Model):
    """Позиция анализа. Данные товара АСУ НСИ хранятся снимком: правка справочника не меняет документ."""

    analysis = models.ForeignKey(MarketingAnalysis, on_delete=models.CASCADE, related_name="items")
    line_no = models.PositiveIntegerField()
    nsi_product = models.ForeignKey(NsiProduct, null=True, on_delete=models.SET_NULL, related_name="+")
    nsi_code = models.CharField("Код АСУ НСИ", max_length=32)
    enstru_code = models.CharField("Код ЕНС ТРУ", max_length=64, blank=True)
    name = models.CharField("Наименование", max_length=500)
    characteristics = models.TextField("Краткая характеристика", blank=True)
    unit = models.CharField("Ед. изм.", max_length=32)
    quantity = models.DecimalField("Количество", max_digits=18, decimal_places=3)
    delivery_place = models.CharField("Место поставки", max_length=500, blank=True)
    delivery_term = models.CharField("Срок поставки", max_length=255, blank=True)
    marketing_price = models.DecimalField(
        "Маркетинговая цена за ед. без НДС, KZT", max_digits=18, decimal_places=2, null=True, blank=True
    )
    total_wo_vat = models.DecimalField("Сумма без НДС, KZT", max_digits=20, decimal_places=2, null=True, blank=True)
    calc_method = models.CharField(max_length=16, blank=True)
    price_justification = models.TextField("Обоснование цены по позиции", blank=True)

    class Meta:
        ordering = ["line_no", "id"]
        constraints = [models.UniqueConstraint(fields=["analysis", "line_no"], name="uniq_ma_item_line")]


class ItemAttachment(models.Model):
    """Вложения к позиции: ТС, чертежи."""

    item = models.ForeignKey(MarketingAnalysisItem, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=upload_attachment_to)
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class CommercialOffer(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Загружено маркетологом"
        SYSTEM = "system", "Получено через систему"

    analysis = models.ForeignKey(MarketingAnalysis, on_delete=models.CASCADE, related_name="offers")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    supplier_name = models.CharField("Поставщик", max_length=500)
    supplier_bin = models.CharField("БИН", max_length=12)
    offer_date = models.DateField("Дата КП")
    currency = models.CharField("Валюта", max_length=3, default="KZT")
    exchange_rate = models.DecimalField("Курс НБ РК на дату КП", max_digits=14, decimal_places=4)
    vat_included = models.BooleanField("Цены с НДС", default=False)
    file = models.FileField(upload_to=upload_offer_to)
    original_name = models.CharField(max_length=255)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.MANUAL)
    kp_request = models.ForeignKey(KpRequest, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class CommercialOfferPrice(models.Model):
    offer = models.ForeignKey(CommercialOffer, on_delete=models.CASCADE, related_name="prices")
    item = models.ForeignKey(MarketingAnalysisItem, on_delete=models.CASCADE, related_name="offer_prices")
    price = models.DecimalField("Цена за ед. в валюте КП", max_digits=18, decimal_places=2)
    price_kzt_wo_vat = models.DecimalField("Цена за ед. KZT без НДС", max_digits=18, decimal_places=2)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["offer", "item"], name="uniq_offer_item_price")]


class AnalysisApprover(models.Model):
    """Согласующие этапа 1, выбранные маркетологом (с порядком)."""

    analysis = models.ForeignKey(MarketingAnalysis, on_delete=models.CASCADE, related_name="approvers")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        constraints = [models.UniqueConstraint(fields=["analysis", "user"], name="uniq_ma_approver")]


class ApprovalStep(models.Model):
    """Шаг маршрута согласования конкретной итерации (отправки)."""

    class StepStatus(models.TextChoices):
        WAITING = "waiting", "Ожидает очереди"
        PENDING = "pending", "На рассмотрении"
        APPROVED = "approved", "Согласовано"
        RETURNED = "returned", "Возвращено на доработку"
        SKIPPED = "skipped", "Не рассматривалось"

    analysis = models.ForeignKey(MarketingAnalysis, on_delete=models.CASCADE, related_name="steps")
    iteration = models.PositiveIntegerField()
    stage = models.PositiveSmallIntegerField(choices=Stage.choices)
    order = models.PositiveIntegerField()
    assignee_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    assignee_role = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=16, choices=StepStatus.choices, default=StepStatus.WAITING)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    decided_by_name = models.CharField(max_length=255, blank=True)
    decided_by_position = models.CharField(max_length=255, blank=True)
    comment = models.TextField(blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["iteration", "stage", "order"]
        indexes = [
            models.Index(fields=["status", "assignee_user"]),
            models.Index(fields=["status", "assignee_role"]),
            models.Index(fields=["analysis", "iteration"]),
        ]
