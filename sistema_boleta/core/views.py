from django.shortcuts import render
from usuarios.models import Usuario
from negocios.models import Negocio
from locales.models import Local, OcupacionLocal
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
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
    

@login_required
def gestion_crud(request):
    """Vista principal del sistema CRUD unificado"""
    
    # Calcular estadísticas del último mes
    hace_un_mes = timezone.now() - timedelta(days=30)
    
    stats = {
        # Totales
        'total_usuarios': Usuario.objects.count(),
        'total_negocios': Negocio.objects.count(),
        'total_locales': Local.objects.count(),
        
        # Creados en el último mes
        'usuarios_mes': Usuario.objects.filter(fechaCreacion__gte=hace_un_mes).count(),
        'negocios_mes': Negocio.objects.filter(fechaCreacion__gte=hace_un_mes).count(),
        'locales_mes': Local.objects.filter(fechaCreacion__gte=hace_un_mes).count(),
    }
    
    return render(request, 'core/gestion_crud.html', {'stats': stats})
