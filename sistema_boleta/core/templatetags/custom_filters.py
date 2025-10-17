from django import template
from locales.models import Local

register = template.Library()


@register.filter
def get_local(locales, posicion):
    print(f"Buscando local con posicionMapa = {posicion}")
    try:
        return next((local for local in locales if local.posicionMapa == int(posicion)), None)
    except Exception as e:
        print(f"Error: {e}")
        return None


@register.filter
def get_ocupacion(ocupaciones, id_local):
    if not ocupaciones or id_local is None:
        return None
    return ocupaciones.get(id_local, None)