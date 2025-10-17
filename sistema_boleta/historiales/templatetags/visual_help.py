from django import template
from datetime import datetime

register = template.Library()

@register.filter
def currency(value):
    """Formatea número como moneda guatemalteca"""
    try:
        return f"Q.{float(value):,.2f}"
    except (ValueError, TypeError):
        return "Q.0.00"
    

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
        return f"{MESES_ES[fecha.month].capitalize()} de {fecha.year}"
    except Exception:
        return value