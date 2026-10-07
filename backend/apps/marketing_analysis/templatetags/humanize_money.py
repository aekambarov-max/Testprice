from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def money(value, digits=2):
    """1234567.5 → «1 234 567,50» (формат, принятый в документах РК)."""
    if value in (None, ""):
        return "—"
    text = f"{Decimal(value):,.{int(digits)}f}"
    return text.replace(",", " ").replace(".", ",")
