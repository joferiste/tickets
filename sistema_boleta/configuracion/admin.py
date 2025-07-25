from django.contrib import admin
from .models import Banco, Configuracion

@admin.register(Banco)
class BancoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero_cuenta')
    search_fields = ('nombre', 'numero_cuenta')
    list_per_page = 10


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ('mora_porcentaje', 'dias_sin_recargo', 'banco_principal', 'activo')
    list_filter = ('mora_porcentaje', 'dias_sin_recargo', 'activo')
    search_fields = ('banco_principal__nombre',)


    def save_model(self, request, obj, form, change):
        """
        Forzamos que solo una configuracion este activa
        """
        if obj.activo:
            Configuracion.objects.exclude(pk=obj.pk).update(activo=False)
        super().save_model(request, obj, form, change)
