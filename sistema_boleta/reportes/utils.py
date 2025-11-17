from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from transacciones.models import Transaccion  # ← IMPORTANTE: Usar Transaccion
from negocios.models import Negocio


def calcular_ingresos_mes(year, month):
    """
    Calcula los ingresos totales de un mes específico.
    Solo cuenta transacciones ÚNICAS con estado 'exitosa' y 'espera_acreditacion'.
    
    Returns:
        dict: {
            'total': Decimal,
            'cantidad_transacciones': int,
            'promedio_por_transaccion': Decimal
        }
    """
    periodo = f"{year}-{month:02d}"
    
    # Usar directamente la tabla Transaccion con estado actual
    resultado = Transaccion.objects.filter(
        periodo_pagado=periodo,
        estado__in=['exitosa', 'espera_acreditacion']  # Solo contar las que están exitosas y espera_acreditacion
    ).aggregate(
        total=Sum('monto'),
        cantidad=Count('idTransaccion')
    )
    
    total = resultado['total'] or Decimal('0')
    cantidad = resultado['cantidad'] or 0
    promedio = (total / cantidad) if cantidad > 0 else Decimal('0')
    
    return {
        'total': total,
        'cantidad_transacciones': cantidad,
        'promedio_por_transaccion': promedio
    }


def calcular_comparacion_mes_anterior(year, month):
    """
    Compara ingresos del mes actual con el mes anterior.
    
    Returns:
        dict: {
            'mes_actual': Decimal,
            'mes_anterior': Decimal,
            'diferencia': Decimal,
            'porcentaje_cambio': float
        }
    """
    # Mes actual
    ingresos_actual = calcular_ingresos_mes(year, month)
    
    # Calcular mes anterior
    if month == 1:
        year_anterior = year - 1
        mes_anterior = 12
    else:
        year_anterior = year
        mes_anterior = month - 1
    
    ingresos_anterior = calcular_ingresos_mes(year_anterior, mes_anterior)
    
    # Calcular diferencia y porcentaje
    diferencia = ingresos_actual['total'] - ingresos_anterior['total']
    
    if ingresos_anterior['total'] > 0:
        porcentaje = float((diferencia / ingresos_anterior['total']) * 100)
    else:
        porcentaje = 100.0 if ingresos_actual['total'] > 0 else 0.0
    
    return {
        'mes_actual': ingresos_actual['total'],
        'mes_anterior': ingresos_anterior['total'],
        'diferencia': diferencia,
        'porcentaje_cambio': round(porcentaje, 2)
    }


def calcular_ingresos_por_estado(year, month):
    """
    Desglosa ingresos por estado ACTUAL de transacción.
    Usa el estado actual de la tabla Transaccion (más simple y eficiente).
    
    Returns:
        dict: {
            'exitosa': {'total': Decimal, 'cantidad': int, 'porcentaje': float},
            'espera_confirmacion': {...},
            ...
        }
    """
    periodo = f"{year}-{month:02d}"
    
    # Obtener todas las transacciones del período y agrupar por estado ACTUAL
    # Esto usa el estado actual de la tabla Transaccion, no del historial
    transacciones = Transaccion.objects.filter(
        periodo_pagado=periodo
    ).values('estado').annotate(
        total=Sum('monto'),
        cantidad=Count('idTransaccion')
    )
    
    # Total general para calcular porcentajes
    total_general = Transaccion.objects.filter(
        periodo_pagado=periodo
    ).aggregate(Sum('monto'))['monto__sum'] or Decimal('0')
    
    resultado = {}
    for trans in transacciones:
        estado_nombre = trans['estado'] or 'sin_estado'
        total = trans['total'] or Decimal('0')
        cantidad = trans['cantidad'] or 0
        porcentaje = float((total / total_general) * 100) if total_general > 0 else 0.0
        
        resultado[estado_nombre] = {
            'total': total,
            'cantidad': cantidad,
            'porcentaje': round(porcentaje, 2)
        }
    
    return resultado


def calcular_ingresos_por_negocio(year, month):
    """
    Calcula ingresos por cada negocio en el mes.
    Usa el estado ACTUAL de cada transacción.
    
    Returns:
        list: [
            {
                'negocio_id': int,
                'negocio_nombre': str,
                'total': Decimal,
                'cantidad': int,
                'con_mora': int,
                'estado': str ('al_dia' o 'mora')
            }
        ]
    """
    periodo = f"{year}-{month:02d}"
    
    # Agrupar por negocio usando estado ACTUAL de transacciones
    ingresos = Transaccion.objects.filter(
        periodo_pagado=periodo,
        estado__in=['exitosa', 'espera_acreditacion']  # Solo exitosas y espera_acreditacion
    ).values(
        'negocio__idNegocio',
        'negocio__nombre'
    ).annotate(
        total=Sum('monto'),
        cantidad=Count('idTransaccion'),
        con_mora=Count('idTransaccion', filter=Q(mora_monto__gt=0))
    ).order_by('-total')
    
    resultado = []
    for item in ingresos:
        resultado.append({
            'negocio_id': item['negocio__idNegocio'],
            'negocio_nombre': item['negocio__nombre'],
            'total': item['total'] or Decimal('0'),
            'cantidad': item['cantidad'] or 0,
            'con_mora': item['con_mora'] or 0,
            'estado': 'mora' if item['con_mora'] > 0 else 'al_dia'
        })
    
    return resultado


def calcular_evolucion_diaria(year, month):
    """
    Calcula la evolución de ingresos día a día en el mes.
    Usa la fecha de la transacción (fechaTransaccion).
    
    Returns:
        list: [
            {'dia': 1, 'total': Decimal, 'acumulado': Decimal},
            {'dia': 2, 'total': Decimal, 'acumulado': Decimal},
            ...
        ]
    """
    from django.db.models.functions import ExtractDay
    from calendar import monthrange
    
    periodo = f"{year}-{month:02d}"
    
    # Obtener todas las transacciones exitosas y con espera_acreditacion del mes agrupadas por día
    transacciones = Transaccion.objects.filter(
        periodo_pagado=periodo,
        estado__in=['exitosa', 'espera_acreditacion']
    ).annotate(
        dia=ExtractDay('fechaTransaccion')  # Usar fecha de transacción
    ).values('dia').annotate(
        total=Sum('monto')
    ).order_by('dia')
    
    # Crear diccionario de días
    dias_dict = {t['dia']: t['total'] for t in transacciones}
    
    # Calcular días del mes
    dias_en_mes = monthrange(year, month)[1]
    
    # Construir lista completa con acumulado
    resultado = []
    acumulado = Decimal('0')
    
    for dia in range(1, dias_en_mes + 1):
        total_dia = dias_dict.get(dia, Decimal('0'))
        acumulado += total_dia
        
        resultado.append({
            'dia': dia,
            'total': total_dia,
            'acumulado': acumulado
        })
    
    return resultado


def calcular_estadisticas_mora(year, month):
    """
    Calcula estadísticas relacionadas con moras.
    Usa transacciones ÚNICAS con estado exitosa.
    
    Returns:
        dict: {
            'total_mora': Decimal,
            'transacciones_con_mora': int,
            'promedio_dias_retraso': float,
            'negocios_con_mora': int
        }
    """
    periodo = f"{year}-{month:02d}"
    
    estadisticas = Transaccion.objects.filter(
        periodo_pagado=periodo,
        estado__in=['exitosa', 'espera_acreditacion'],
        mora_monto__gt=0
    ).aggregate(
        total_mora=Sum('mora_monto'),
        cantidad=Count('idTransaccion'),
        promedio_dias=Avg('dias_retraso'),
        negocios=Count('negocio', distinct=True)
    )
    
    return {
        'total_mora': estadisticas['total_mora'] or Decimal('0'),
        'transacciones_con_mora': estadisticas['cantidad'] or 0,
        'promedio_dias_retraso': round(estadisticas['promedio_dias'] or 0, 1),
        'negocios_con_mora': estadisticas['negocios'] or 0
    }


def obtener_top_negocios(year, month, limit=5):
    """
    Obtiene los negocios con mayores ingresos en el mes.
    
    Returns:
        list: Top N negocios ordenados por ingresos
    """
    ingresos = calcular_ingresos_por_negocio(year, month)
    return ingresos[:limit]


def calcular_resumen_mes(year, month):
    """
    Función principal que retorna un resumen completo del mes.
    Útil para el dashboard principal.
    
    Returns:
        dict: Resumen completo con todas las métricas
    """
    ingresos = calcular_ingresos_mes(year, month)
    comparacion = calcular_comparacion_mes_anterior(year, month)
    por_estado = calcular_ingresos_por_estado(year, month)
    por_negocio = calcular_ingresos_por_negocio(year, month)
    mora = calcular_estadisticas_mora(year, month)
    
    return {
        'periodo': f"{year}-{month:02d}",
        'ingresos': ingresos,
        'comparacion': comparacion,
        'por_estado': por_estado,
        'por_negocio': por_negocio,
        'mora': mora,
        'top_negocios': obtener_top_negocios(year, month, 5)
    }


def formatear_moneda(monto):
    """
    Formatea un monto a formato de moneda guatemalteca.
    
    Args:
        monto: Decimal o float
    
    Returns:
        str: "Q 5,000.00"
    """
    return f"Q {monto:,.2f}"


def formatear_porcentaje(valor):
    """
    Formatea un porcentaje con signo.
    
    Args:
        valor: float
    
    Returns:
        str: "+12.5%" o "-5.3%"
    """
    signo = '+' if valor >= 0 else ''
    return f"{signo}{valor:.1f}%"