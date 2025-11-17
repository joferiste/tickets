from django import template

register = template.Library()

@register.filter
def to(start, end):
    return range(start, end + 1)


@register.filter
def formato_q(value):
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return "0.00"