from django.contrib import admin
from .models import HistorialTransaccion, HistorialBase, HistorialLocal, HistorialNegocio

admin.site.register(HistorialTransaccion)
admin.site.register(HistorialLocal)
admin.site.register(HistorialNegocio)

