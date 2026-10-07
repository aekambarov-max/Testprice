"""Роли подмодуля и матрица доступа (раздел 4 ТЗ).

Роли хранятся как группы Django; группы создаются миграцией core.0002_roles.
«Согласующий ДЗО» — не роль, а участие в маршруте конкретного анализа.
"""

MARKETER = "marketer"  # Маркетолог / Ответственный за маркетинг цен ДЗО
DB_SPECIALIST = "db_specialist"  # Специалист ДБ КМГ
DB_DIRECTOR = "db_director"  # Директор ДБ КМГ
ADMIN = "ma_admin"  # Администратор подмодуля

ROLE_TITLES = {
    MARKETER: "Маркетолог (Ответственный за маркетинг цен ДЗО)",
    DB_SPECIALIST: "Специалист ДБ КМГ",
    DB_DIRECTOR: "Директор ДБ КМГ",
    ADMIN: "Администратор",
}

ALL_ROLES = tuple(ROLE_TITLES)


def user_roles(user):
    """Множество кодов ролей пользователя (кэшируется на объекте на время запроса)."""
    if not user or not user.is_authenticated:
        return frozenset()
    cached = getattr(user, "_price_roles", None)
    if cached is None:
        cached = frozenset(user.groups.filter(name__in=ALL_ROLES).values_list("name", flat=True))
        if user.is_superuser:
            cached = cached | {ADMIN}
        user._price_roles = cached
    return cached


def has_role(user, role):
    return role in user_roles(user)


def is_admin(user):
    return has_role(user, ADMIN)
