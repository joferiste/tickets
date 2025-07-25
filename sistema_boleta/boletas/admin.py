from django.contrib import admin
from .models import Boleta, TipoPago, EstadoBoleta, BoletaSandbox

admin.site.register(Boleta)
admin.site.register(TipoPago)
admin.site.register(EstadoBoleta)
admin.site.register(BoletaSandbox)