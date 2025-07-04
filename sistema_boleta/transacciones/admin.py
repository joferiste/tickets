from django.contrib import admin
from transacciones.models import Transaccion, EstadoTransaccion


admin.site.register(Transaccion)
admin.site.register(EstadoTransaccion)

