"""Демо-данные для тестового стенда: ДЗО, пользователи пяти ролей, товары АСУ НСИ, пул поставщиков,
курсы НБ РК и история каталога цен. Повторный запуск безопасен.

    python manage.py seed_demo [--password ПАРОЛЬ]
"""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core import roles
from apps.core.models import CurrencyRate, Dzo, UserProfile
from apps.nsi.models import NsiProduct
from apps.pricing.models import PriceCatalogEntry
from apps.suppliers.models import Supplier

DZOS = [
    ("EMG", "АО «Эмбамунайгаз»", "«Ембімұнайгаз» АҚ"),
    ("MMG", "АО «Мангистаумунайгаз»", "«Маңғыстаумұнайгаз» АҚ"),
    ("OMG", "АО «Озенмунайгаз»", "«Өзенмұнайгаз» АҚ"),
    ("KMG", "АО НК «КазМунайГаз» (корпоративный центр)", "«ҚазМұнайГаз» ҰК АҚ (корпоративтік орталық)"),
]

# username, фамилия, имя, отчество, должность, подразделение, ДЗО, роли
USERS = [
    ("marketer", "Ахметова", "Динара", "Серикболовна", "Ответственный за маркетинг цен", "Отдел закупок", "EMG",
     [roles.MARKETER]),
    ("approver1", "Нурланов", "Ерлан", "Каиргалиевич", "Начальник отдела МТО", "Отдел МТО", "EMG", []),
    ("approver2", "Сейткалиева", "Айгерим", "Маратовна", "Главный экономист", "Планово-экономический отдел", "EMG", []),
    ("initiator", "Жумабаев", "Арман", "Болатович", "Главный механик", "Управление добычи", "EMG", []),
    ("db_specialist", "Касымова", "Гульнар", "Ертаевна", "Главный специалист ДБ", "Департамент бюджетирования", "KMG",
     [roles.DB_SPECIALIST]),
    ("db_director", "Тлеуов", "Бауыржан", "Кайратович", "Директор департамента бюджетирования",
     "Департамент бюджетирования", "KMG", [roles.DB_DIRECTOR]),
    ("ma_admin", "Администратор", "Системы", "", "Администратор ИС Price", "ДИТ", "KMG", [roles.ADMIN]),
    ("marketer_mmg", "Иманова", "Салтанат", "Ерболовна", "Ответственный за маркетинг цен", "Отдел закупок", "MMG",
     [roles.MARKETER]),
]

PRODUCTS = [
    ("1010101001", "222011.100.000001", "Труба стальная бесшовная 89х6 мм", "ГОСТ 8732-78, сталь 20", "м"),
    ("1010101002", "222011.100.000002", "Труба насосно-компрессорная 73х5,5 мм", "ГОСТ 633-80, группа прочности Д", "м"),
    ("2020202001", "281314.300.000010", "Насос штанговый скважинный НН2Б-44", "Для добычи нефти, ход 3 м", "шт"),
    ("2020202002", "281314.300.000011", "Штанга насосная ШН-22", "Сталь 20Н2М, длина 8 м", "шт"),
    ("3030303001", "192029.900.000005", "Масло моторное 10W-40", "Канистра 20 л, API CI-4", "л"),
    ("3030303002", "201513.500.000001", "Ингибитор коррозии", "Для нефтепромысловых сред", "кг"),
    ("4040404001", "141210.000.000015", "Костюм рабочий летний", "Хлопок 100%, СИЗ, с СВП", "компл"),
    ("4040404002", "152012.000.000003", "Ботинки кожаные с металлическим подноском", "ГОСТ 28507-90", "пара"),
]

SUPPLIERS = [
    ("050140000011", "ТОО «КазТрубСнаб»", "sales@kaztrubsnab.example"),
    ("060240000027", "ТОО «Атырау Нефтемаш»", "kp@atyraunm.example"),
    ("070340000032", "ТОО «Каспий Ойл Сервис»", "offers@caspianos.example"),
    ("080440000048", "ТОО «Спецодежда Актау»", "tender@sodaktau.example"),
    ("090540000053", "ТОО «Мунай Химия»", "info@munaychem.example"),
]

RATES = {"USD": Decimal("505.20"), "EUR": Decimal("590.40"), "RUB": Decimal("6.25"), "CNY": Decimal("70.80")}

HISTORY = [
    ("1010101001", "MMG", Decimal("7850.00"), 120),
    ("1010101001", "OMG", Decimal("8120.00"), 60),
    ("2020202001", "MMG", Decimal("1450000.00"), 200),
    ("3030303001", "OMG", Decimal("2150.00"), 30),
]


class Command(BaseCommand):
    help = "Заполнить демо-данные для тестового стенда"

    def add_arguments(self, parser):
        parser.add_argument("--password", default="Demo12345!", help="Пароль демо-пользователей")

    def handle(self, *args, password, **options):
        dzos = {}
        for code, name_ru, name_kk in DZOS:
            dzos[code], _ = Dzo.objects.update_or_create(code=code, defaults={"name_ru": name_ru, "name_kk": name_kk})
        User = get_user_model()
        for username, last, first, middle, position, department, dzo, user_roles in USERS:
            user, created = User.objects.get_or_create(username=username, defaults={
                "last_name": last, "first_name": first, "email": f"{username}@price.local"})
            if created:
                user.set_password(password)
            if roles.ADMIN in user_roles:
                user.is_staff = user.is_superuser = True
            user.save()
            profile, _ = UserProfile.objects.update_or_create(user=user, defaults={
                "middle_name": middle, "position": position, "department": department, "dzo": dzos[dzo]})
            for role in user_roles:
                user.groups.add(Group.objects.get(name=role))
        for nsi_code, enstru, name, descr, unit in PRODUCTS:
            NsiProduct.objects.update_or_create(nsi_code=nsi_code, defaults={
                "enstru_code": enstru, "name": name, "short_description": descr, "unit": unit})
        for bin_, name, email in SUPPLIERS:
            Supplier.objects.update_or_create(bin=bin_, defaults={"name": name, "email": email})
        today = date.today()
        for delta in range(0, 400, 7):
            for code, rate in RATES.items():
                CurrencyRate.objects.get_or_create(date=today - timedelta(days=delta), currency=code,
                                                   defaults={"rate": rate})
        for nsi_code, dzo, price, days_ago in HISTORY:
            product = NsiProduct.objects.get(nsi_code=nsi_code)
            PriceCatalogEntry.objects.get_or_create(
                nsi_code=nsi_code, dzo=dzos[dzo], source_type="legacy", source_id=f"{nsi_code}-{dzo}",
                defaults={"enstru_code": product.enstru_code, "name": product.name, "unit": product.unit,
                          "price_wo_vat": price, "approved_at": timezone.now() - timedelta(days=days_ago),
                          "source_number": f"ID{today.year - 1}.{dzo}.{days_ago:04d}"})
        self.stdout.write(self.style.SUCCESS(
            f"Демо-данные готовы. Пользователи: {', '.join(u[0] for u in USERS)}; пароль: {password}"))
