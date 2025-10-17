from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from negocios.models import Negocio
from historiales.models import PerfilPagoNegocio
from historiales.metrics import actualizar_metricas_negocio, obtener_historial_timeline
from transacciones.models import Transaccion
from django.db.models import Q
from collections import defaultdict
from datetime import datetime, timedelta
from django.utils import timezone
import json

def dashboard_metricas(request):
    """
    Vista principal del dashboard de metricas
    Muestra buscador de negocios y, si se selecciona uno, sus metricas
    """

    negocio_seleccionado = None
    perfil = None
    timeline = None
    estadisticas = None

    # Si se selecciona un negocio
    negocio_id = request.GET.get('negocio_id')
    if negocio_id:
        negocio_seleccionado = get_object_or_404(Negocio, idNegocio=negocio_id)

        # Obtener o crear perfil
        perfil, created = PerfilPagoNegocio.objects.get_or_create(negocio=negocio_seleccionado)

        debe_recalcular = (
            created or
            not perfil.ultima_actualizacion or 
            (timezone.now() - perfil.ultima_actualizacion) > timedelta(minutes=3)
        )

        if debe_recalcular:
            actualizar_metricas_negocio(negocio_seleccionado)
            perfil.refresh_from_db() 

        # Obtener timeline
        timeline = obtener_historial_timeline(negocio_seleccionado)

        # Calcular estadisticas adicionales para graficos
        transacciones = Transaccion.objects.filter(
            negocio=negocio_seleccionado,
            estado='exitosa'
        ).order_by('fechaTransaccion')

        # Datos para grafico de linea (ultimos 12 meses)
        pagos_por_mes = defaultdict(lambda: {'monto': 0, 'count': 0})

        total_efectivo = perfil.total_pago_efectivo if perfil else 0
        total_no_efectivo = (perfil.total_pagos_realizados - total_efectivo) if perfil else 0
        
        for t in transacciones:
            mes_key = t.fechaTransaccion.strftime('%Y-%m')
            pagos_por_mes[mes_key]['monto'] += float(t.monto)
            pagos_por_mes[mes_key]['count'] += 1

        # ultimos 12 meses ordenados
        meses_ordenados = sorted(pagos_por_mes.keys())[-12:]

        # Calcular totales
        total_efectivo = perfil.total_pago_efectivo if perfil else 0
        total_no_efectivo = (perfil.total_pago_cheque + perfil.total_pago_deposito) if perfil else 0

        estadisticas = {
            'meses_labels': json.dumps([datetime.strptime(m, '%Y-%m').strftime('%b %Y') for m in meses_ordenados]),
            'meses_montos': json.dumps([pagos_por_mes[m]['monto'] for m in meses_ordenados]),
            'meses_cantidad': json.dumps([pagos_por_mes[m]['count'] for m in meses_ordenados]),

            # Metodos de pago para grafico de pie
            'metodos': {
                'efectivo': total_efectivo,
                'no_efectivo': total_no_efectivo,
            },

            # cards secundarias la separación cheque/deposito
            'detallados': {
                'cheque': perfil.total_pago_cheque if perfil else 0,
                'deposito': perfil.total_pago_deposito if perfil else 0,
            },

            # Distribución mora vs sin mora
            'pagos_con_mora': perfil.total_veces_con_mora if perfil else 0,
            'pagos_sin_mora': (perfil.total_pagos_realizados - perfil.total_veces_con_mora) if perfil else 0,
        }

    # Lista de negocios con transacciones exitosas
    negocios_ids = Transaccion.objects.filter(
        estado='exitosa'
    ).values_list('negocio_id', flat=True).distinct()

    print("=" * 50)
    print(f"IDs de negocios con transacciones exitosas: {list(negocios_ids)}")
    print(f"Total IDs encontrados: {len(negocios_ids)}")

    # Lista de negocios para el buscador 
    negocios_disponibles = Negocio.objects.filter(
        estado__nombre='Activo',
        idNegocio__in=negocios_ids  
    ).order_by('nombre')

    print(f"Negocios disponibles: {negocios_disponibles.count()}")
    for neg in negocios_disponibles:
        print(f"  - {neg.nombre} (ID: {neg.idNegocio})")
    print("=" * 50)

    contexto = {
        'negocios_disponibles': negocios_disponibles,
        'negocio_seleccionado': negocio_seleccionado,
        'perfil': perfil,
        'timeline': timeline,
        'estadisticas': estadisticas,
    }
    
    
    return render(request, 'historiales/dashboard_metricas.html', contexto)


def buscar_negocios_ajax(request):
    """Endpoint AJAX para busqueda de negocios"""

    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    negocios = Negocio.objects.filter(
        Q(nombre__icontains=query) | Q(usuario__nombre__icontains=query),
        estado='activo'
    ).values('idNegocio', 'nombre')[:10]
    
    return JsonResponse({
        'results': list(negocios)
    })