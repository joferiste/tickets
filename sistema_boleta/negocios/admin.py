from django.contrib import admin
from negocios.models import Negocio, EstadoNegocio, Categoria

admin.site.register(Negocio)
admin.site.register(EstadoNegocio)
admin.site.register(Categoria)

