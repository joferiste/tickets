from django.shortcuts import render
from negocios.models import Negocio
from locales.models import Local, OcupacionLocal

def home(request):
    negocios = Negocio.objects.select_related('usuario').filter(estado__nombre="Activo")
    locales = Local.objects.select_related('nivel', 'estado').prefetch_related('ocupaciones__negocio') # Locales existentes con su ocupacion actual
    
    # Se filtran las ocupaciones vigentes (fecha_fin es None o posterior a hoy)
    ocupaciones_vigentes = {
        ocupacion.local.idLocal: ocupacion
        for ocupacion in OcupacionLocal.objects.select_related('negocio', 'local').filter(fecha_fin__isnull=True)
    }

    return render(request, 'core/home.html', {'negocios': negocios,
                                                'locales': locales,
                                                'ocupaciones': ocupaciones_vigentes})
    
 