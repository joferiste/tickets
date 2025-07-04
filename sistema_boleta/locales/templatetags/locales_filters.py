from django import template
from locales.models import Local

register = template.Library()

@register.filter
def add_disabled(field, condition):
    # Filtro usado en campos de formulario (BoundField)
    if condition:
        field.field.widget.attrs['disabled'] = 'disabled'
    return field



@register.filter
def add_disabled_attr(condition):
    # Filtro genérico para atributos HTML (botones, enlaces, etc...)
    return 'disabled="disabled"' if condition else '' 