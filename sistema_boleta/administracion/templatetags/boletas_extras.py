from django import template
from datetime import datetime

register = template.Library()

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}

@register.filter
def periodo_legible(value):
    """
    Convierte 'YYYY-MM' en 'Mes YYYY' en español
    """
    try:
        fecha = datetime.strptime(value, "%Y-%m")
        return f"{MESES_ES[fecha.month].capitalize()} {fecha.year}"
    except Exception:
        return value
    

@register.filter
def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0
    

@register.filter
def formato_q(value):
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return "0.00"