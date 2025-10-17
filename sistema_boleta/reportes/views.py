from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from negocios.models import Negocio 
from locales.models import Local
from historiales.models import HistorialNegocio, HistorialLocal
from .utils import (
    calcular_resumen_mes,
    calcular_evolucion_diaria,
    calcular_ingresos_por_negocio,
    formatear_moneda,
    formatear_porcentaje
)



@login_required(login_url='login')  
def consolidado_ingresos(request):
    """
    Vista principal del reporte consolidado de ingresos.
    Muestra métricas generales, gráficos y tablas de negocios.
    """
    # Obtener mes y año de los parametros GET o usar el actual
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))

    # Validar mes y año
    if month < 1 or month > 12:
        month = now.month
    if year < 2020 or year > now.year + 1:
        year = now.year

    # Obtener resumen completo del mes
    resumen = calcular_resumen_mes(year, month)

    # Obtener evolucion diario por graficos
    evolucion_diaria = calcular_evolucion_diaria(year, month)

    # Preparar datos para graficos (formato JSON)
    # Grafico de lineas - Evolucion diaria
    labels_evolucion = [item['dia'] for item in evolucion_diaria]
    datos_diarios = [float(item['total']) for item in evolucion_diaria]
    datos_acumulados = [float(item['acumulado']) for item in evolucion_diaria]

    # Grafico de barras  Top negocios
    top_negocios = resumen['top_negocios']
    labels_negocios = [n['negocio_nombre'] for n in top_negocios]
    datos_negocios = [float(n['total']) for n in top_negocios]

    #Graficos de pie - Estados de transacciones
    estados_data = resumen['por_estado']
    labels_estado = []
    datos_estado = []
    colores_estado = {
        'exitosa': "#4f6ced",
        'en_revision': "#f878a7",
        'procesada': "#16bcd5",
        'espera_confirmacion': "#6bef89",
        'espera_confirmacion_faltante': "#377d65",
        'espera_complemento': "#d0ed2c",
        'espera_acreditacion': "#f46e65",
        'pendiente': '#6c757d',
        'rechazada': '#dc3545'
    }
    colores_list = []

    for estado, datos in estados_data.items():
        labels_estado.append(estado.replace('_', ' ').title())
        datos_estado.append(float(datos['total']))
        colores_list.append(colores_estado.get(estado, '#6c757d'))

    # Preparar nombres de meses para selector
    meses = [
        {'num': 1, 'nombre': 'Enero'},
        {'num': 2, 'nombre': 'Febrero'},
        {'num': 3, 'nombre': 'Marzo'},
        {'num': 4, 'nombre': 'Abril'},
        {'num': 5, 'nombre': 'Mayo'},
        {'num': 6, 'nombre': 'Junio'},
        {'num': 7, 'nombre': 'Julio'},
        {'num': 8, 'nombre': 'Agosto'},
        {'num': 9, 'nombre': 'Septiembre'},
        {'num': 10, 'nombre': 'Octubre'},
        {'num': 11, 'nombre': 'Noviembre'},
        {'num': 12, 'nombre': 'Diciembre'},
    ]

    # Años disponibles (desde 2020 hasta año actual + 1)
    years = list(range(2020, now.year + 2))
    
    context = {
        'year': year,
        'month': month,
        'mes_nombre': meses[month - 1]['nombre'],
        'meses': meses,
        'years': years,
        'resumen': resumen,
        'evolucion_diaria': evolucion_diaria,
        
        # Datos para gráficos
        'chart_evolucion': {
            'labels': labels_evolucion,
            'datos_diarios': datos_diarios,
            'datos_acumulados': datos_acumulados
        },
        'chart_negocios': {
            'labels': labels_negocios,
            'datos': datos_negocios
        },
        'chart_estados': {
            'labels': labels_estado,
            'datos': datos_estado,
            'colores': colores_list
        },
        
        # Funciones de formato
        'formatear_moneda': formatear_moneda,
        'formatear_porcentaje': formatear_porcentaje,
    }
    
    return render(request, 'reportes/consolidado_ingresos.html', context)


@login_required
def historial_negocio(request, negocio_id):
    """Vista para mostrar el historial completo de un negocio"""
    negocio = get_object_or_404(Negocio, idNegocio=negocio_id)
    
    # Obtener historial ordenado por fecha (más reciente primero)
    historial = HistorialNegocio.objects.filter(negocio=negocio).order_by('-fechaModificacion')
    
    # Paginación (10 registros por página)
    paginator = Paginator(historial, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener ocupación actual si existe
    ocupacion_actual = negocio.ocupacionlocal_set.filter(fecha_fin__isnull=True).first()
    
    context = {
        'negocio': negocio,
        'page_obj': page_obj,
        'ocupacion_actual': ocupacion_actual,
        'total_registros': historial.count()
    }
    
    return render(request, 'reportes/historial_negocios.html', context)


@login_required
def historial_local(request, local_id):
    """Vista para mostrar el historial completo de un local"""
    local = get_object_or_404(Local, idLocal=local_id)
    
    # Obtener historial ordenado por fecha (más reciente primero)
    historial = HistorialLocal.objects.filter(local=local).order_by('-fechaModificacion')
    
    # Paginación (10 registros por página)
    paginator = Paginator(historial, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener ocupación actual si existe
    ocupacion_actual = local.ocupaciones.filter(fecha_fin__isnull=True).first()
    
    context = {
        'local': local,
        'page_obj': page_obj,
        'ocupacion_actual': ocupacion_actual,
        'total_registros': historial.count()
    }
    
    return render(request, 'reportes/historial_locales.html', context)