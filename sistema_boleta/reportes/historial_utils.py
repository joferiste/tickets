"""
Funciones auxiliares para consultar el historial de transacciones.
Agregar a: reportes/utils.py o crear archivo reportes/historial_utils.py
"""

from historiales.models import HistorialTransaccion
from transacciones.models import Transaccion
from django.db.models import Q


def obtener_historial_por_negocio_periodo(negocio_nombre, periodo):
    """
    Obtiene todo el historial de transacciones de un negocio en un período específico.
    
    Args:
        negocio_nombre: str - Nombre del negocio (ej: "Cafeteria Los Alamos")
        periodo: str - Período en formato YYYY-MM (ej: "2025-10")
    
    Returns:
        QuerySet de HistorialTransaccion ordenado cronológicamente
        
    Ejemplo:
        >>> historial = obtener_historial_por_negocio_periodo("Cafeteria Los Alamos", "2025-10")
        >>> for h in historial:
        >>>     print(f"{h.fechaModificacion} - {h.accion} - {h.estadoNuevo}")
    """
    return HistorialTransaccion.objects.filter(
        transaccion__negocio__nombre__icontains=negocio_nombre,
        periodo_pagado=periodo
    ).select_related('transaccion', 'transaccion__negocio').order_by('fechaModificacion')


def obtener_historial_por_transaccion_id(transaccion_id):
    """
    Obtiene todo el historial de una transacción específica por su ID.
    
    Args:
        transaccion_id: int - ID de la transacción
    
    Returns:
        QuerySet de HistorialTransaccion
        
    Ejemplo:
        >>> historial = obtener_historial_por_transaccion_id(123)
        >>> print(f"Total de cambios: {historial.count()}")
    """
    return HistorialTransaccion.objects.filter(
        transaccion_id=transaccion_id
    ).order_by('fechaModificacion')


def obtener_historial_por_transaccion_nombre(transaccion_nombre):
    """
    Obtiene todo el historial de una transacción por su nombre.
    
    Args:
        transaccion_nombre: str - Nombre único de la transacción
        
    Returns:
        QuerySet de HistorialTransaccion
        
    Ejemplo:
        >>> historial = obtener_historial_por_transaccion_nombre("TRANSACCION-123-cafeteria-20251008")
    """
    return HistorialTransaccion.objects.filter(
        transaccion__nombre=transaccion_nombre
    ).order_by('fechaModificacion')


def obtener_linea_tiempo_completa(negocio_nombre, periodo):
    """
    Genera una línea de tiempo visual del historial de un negocio en un período.
    
    Args:
        negocio_nombre: str
        periodo: str - YYYY-MM
    
    Returns:
        list: [
            {
                'fecha': datetime,
                'transaccion_nombre': str,
                'accion': str,
                'estado': str,
                'descripcion': str,
                'monto': Decimal,
                'metodo_pago': str,
                'observaciones': str,
                'color': str  # Para UI
            }
        ]
    """
    historial = obtener_historial_por_negocio_periodo(negocio_nombre, periodo)
    
    colores = {
        'CREACION': 'primary',
        'CAMBIO': 'success',
        'ACTUALIZACION': 'info'
    }
    
    linea_tiempo = []
    for h in historial:
        linea_tiempo.append({
            'fecha': h.fechaModificacion,
            'transaccion_nombre': h.transaccion.nombre,
            'accion': h.accion,
            'estado': h.estadoNuevo,
            'descripcion': h.descripcion,
            'monto': h.monto,
            'metodo_pago': h.metodo_pago,
            'observaciones': h.observaciones,
            'color': colores.get(h.accion, 'secondary')
        })
    
    return linea_tiempo


def resumen_historial_negocio(negocio_nombre, periodo):
    """
    Genera un resumen estadístico del historial de un negocio.
    
    Returns:
        dict: {
            'negocio': str,
            'periodo': str,
            'total_cambios': int,
            'cambios_estado': int,
            'actualizaciones': int,
            'transacciones_unicas': int,
            'estados_transitados': list,
            'primer_registro': datetime,
            'ultimo_registro': datetime
        }
    """
    historial = obtener_historial_por_negocio_periodo(negocio_nombre, periodo)
    
    if not historial.exists():
        return None
    
    cambios_estado = historial.filter(accion='CAMBIO').count()
    actualizaciones = historial.filter(accion='ACTUALIZACION').count()
    
    # Estados únicos por los que pasó
    estados = historial.values_list('estadoNuevo', flat=True).distinct()
    
    # Transacciones únicas
    transacciones_unicas = historial.values('transaccion').distinct().count()
    
    return {
        'negocio': negocio_nombre,
        'periodo': periodo,
        'total_cambios': historial.count(),
        'cambios_estado': cambios_estado,
        'actualizaciones': actualizaciones,
        'transacciones_unicas': transacciones_unicas,
        'estados_transitados': list(estados),
        'primer_registro': historial.first().fechaModificacion,
        'ultimo_registro': historial.last().fechaModificacion
    }


def buscar_en_historial(texto, periodo=None):
    """
    Busca texto en descripciones y observaciones del historial.
    
    Args:
        texto: str - Texto a buscar
        periodo: str (opcional) - YYYY-MM
    
    Returns:
        QuerySet de HistorialTransaccion que contienen el texto
        
    Ejemplo:
        >>> # Buscar todas las veces que se mencionó "confirmación"
        >>> resultados = buscar_en_historial("confirmación", "2025-10")
    """
    query = Q(descripcion__icontains=texto) | Q(observaciones__icontains=texto)
    
    historial = HistorialTransaccion.objects.filter(query)
    
    if periodo:
        historial = historial.filter(periodo_pagado=periodo)
    
    return historial.select_related('transaccion', 'transaccion__negocio').order_by('-fechaModificacion')


def obtener_cambios_por_tipo(negocio_nombre=None, periodo=None, tipo_cambio=None):
    """
    Filtra historial por tipo de cambio específico.
    
    Args:
        negocio_nombre: str (opcional)
        periodo: str (opcional) - YYYY-MM
        tipo_cambio: str (opcional) - 'cambio_estado', 'cambio_metodo_pago', etc.
    
    Returns:
        QuerySet filtrado
        
    Ejemplo:
        >>> # Ver todos los cambios de método de pago de octubre
        >>> cambios = obtener_cambios_por_tipo(periodo="2025-10", tipo_cambio="cambio_metodo_pago")
    """
    historial = HistorialTransaccion.objects.all()
    
    if negocio_nombre:
        historial = historial.filter(transaccion__negocio__nombre__icontains=negocio_nombre)
    
    if periodo:
        historial = historial.filter(periodo_pagado=periodo)
    
    if tipo_cambio:
        historial = historial.filter(tipoCambio=tipo_cambio)
    
    return historial.select_related('transaccion', 'transaccion__negocio').order_by('-fechaModificacion')


# ============== EJEMPLOS DE USO ==============

"""
# En la shell de Django o en una vista:

# 1. Ver todo el historial de Cafeteria Los Alamos en octubre 2025
historial = obtener_historial_por_negocio_periodo("Cafeteria Los Alamos", "2025-10")
for h in historial:
    print(f"{h.fechaModificacion.strftime('%Y-%m-%d %H:%M')} - {h.accion} - {h.estadoNuevo}")
    print(f"  Descripción: {h.descripcion}")
    print(f"  Método: {h.metodo_pago}")
    print()

# Salida esperada:
# 2025-10-08 10:00 - CREACION - espera_confirmacion_faltante
#   Descripción: Transacción creada...
#   Método: Cheque Ajeno
# 
# 2025-10-08 10:05 - CAMBIO - espera_complemento
#   Descripción: Cambio de estado: espera_confirmacion_faltante → espera_complemento
#   Método: Efectivo
# 
# 2025-10-08 10:10 - CAMBIO - exitosa
#   Descripción: Cambio de estado: espera_complemento → exitosa. Faltante: Q1000 → Q0
#   Método: Efectivo


# 2. Obtener resumen estadístico
resumen = resumen_historial_negocio("Cafeteria Los Alamos", "2025-10")
print(resumen)

# Salida:
# {
#     'negocio': 'Cafeteria Los Alamos',
#     'periodo': '2025-10',
#     'total_cambios': 3,
#     'cambios_estado': 2,
#     'actualizaciones': 0,
#     'transacciones_unicas': 1,
#     'estados_transitados': ['espera_confirmacion_faltante', 'espera_complemento', 'exitosa'],
#     'primer_registro': datetime(2025, 10, 8, 10, 0),
#     'ultimo_registro': datetime(2025, 10, 8, 10, 10)
# }


# 3. Buscar todas las veces que se mencionó "complemento"
resultados = buscar_en_historial("complemento", "2025-10")
for r in resultados:
    print(f"{r.transaccion.negocio.nombre} - {r.descripcion}")


# 4. Ver todos los cambios de método de pago
cambios_metodo = obtener_cambios_por_tipo(periodo="2025-10", tipo_cambio="cambio_metodo_pago")
for c in cambios_metodo:
    print(f"{c.transaccion.negocio.nombre}: {c.descripcion}")


# 5. Generar línea de tiempo visual
linea_tiempo = obtener_linea_tiempo_completa("Cafeteria Los Alamos", "2025-10")
for item in linea_tiempo:
    print(f"[{item['color']}] {item['fecha']} - {item['accion']}")
    print(f"  Estado: {item['estado']}")
    print(f"  {item['descripcion']}")
    print()
"""