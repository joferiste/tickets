from django.contrib import admin
from .models import HistorialTransaccion, HistorialBase, HistorialLocal, HistorialNegocio, PerfilPagoNegocio

admin.site.register(HistorialTransaccion)
admin.site.register(HistorialLocal)
admin.site.register(HistorialNegocio)
admin.site.register(PerfilPagoNegocio)


