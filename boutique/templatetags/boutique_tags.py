from django import template
register = template.Library()

@register.filter
def rubles(value):
    if value is None:
        return "Цена по запросу"
    amount = f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
    return amount.replace(",", "\u00a0").replace(".", ",") + " ₽"
