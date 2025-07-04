from django import template
from django.urls import resolve

register = template.Library()

@register.simple_tag(takes_context=True)
def active(context, url_name):
    """
    Devuelve 'active' si la vista actual coincide con url_name.
    Se usa de esta forma: class="{% active 'home' %}"
    """
    try:
        return "active" if resolve(context['request'].path).url_name == url_name else ""
    except:
        return ""