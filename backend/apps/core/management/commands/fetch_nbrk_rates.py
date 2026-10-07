"""Загрузка официальных курсов НБ РК на дату: python manage.py fetch_nbrk_rates [--date ДД.ММ.ГГГГ].

Рекомендуется запускать ежедневно (cron / Celery beat).
"""

import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

from apps.core.models import CurrencyRate

NBRK_URL = "https://nationalbank.kz/rss/get_rates.cfm?fdate={date}"


class Command(BaseCommand):
    help = "Загрузить курсы валют НБ РК"

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Дата в формате ДД.ММ.ГГГГ (по умолчанию сегодня)")

    def handle(self, *args, **options):
        on_date = datetime.strptime(options["date"], "%d.%m.%Y").date() if options["date"] else date.today()
        try:
            with urllib.request.urlopen(NBRK_URL.format(date=on_date.strftime("%d.%m.%Y")), timeout=30) as resp:
                root = ET.fromstring(resp.read())
        except Exception as exc:
            raise CommandError(f"НБ РК недоступен: {exc}") from exc
        count = 0
        for item in root.iter("item"):
            code = (item.findtext("title") or "").strip().upper()
            value = (item.findtext("description") or "").strip()
            quant = Decimal((item.findtext("quant") or "1").strip() or "1")
            if len(code) != 3 or not value:
                continue
            CurrencyRate.objects.update_or_create(
                date=on_date, currency=code, defaults={"rate": (Decimal(value) / quant).quantize(Decimal("0.0001"))}
            )
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Загружено курсов: {count} на {on_date:%d.%m.%Y}"))
