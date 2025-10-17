from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def formatear_moneda(monto):
    """
    Formatea un monto a formato de moneda guatemalteca
    Uso {{ monto|formatear_moneda }}
    """

    if monto is None:
        return "Q. 0.00"
    
    try:
        monto_decimal = Decimal(str(monto))
        return f"Q. {monto_decimal:,.2f}"
    except:
        return "Q. 0.00"
    
@register.filter
def formatear_porcentaje(valor):
    """
    Formatear un porcentaje con signo
    Uso {{ valor|formatear_porcentaje }}
    """

    if valor is None:
        return "0.0%"
    
    try:
        valor_float = float(valor)
        signo = '+' if valor_float >= 0 else ''
        return f"{signo}{valor_float:.1f}%"
    except:
        return "0.0%"