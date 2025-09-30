from decimal import Decimal
from django.utils import timezone

def analizar_transaccion_recibo(transaccion):
    """
    Analiza una transaccion y retorna informacion esctructurada para el recibo
    Args:
        transaccion: instancia de transaccion

    Returns:
        dict con informacion detallada para el recibo
    """
    info = {
        'descripcion_principal': '',
        'tiene_mora': False,
        'tiene_excedente': False,
        'tiene_excedentes_aplicados': [],
        'detalles_adicionales': None,
        'notas_especiales': [],
        'estado_especiales': None
    }

    # === === DETALLE DE LA TRANSACCION === ===        
    MESES_ES = {
        "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
        "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
        "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
    }
    periodo_str = str(transaccion.periodo_pagado)
    anio, mes = periodo_str.split('-')
    # Preparar descripcion
    descripcion = f"Pago del mes de {MESES_ES[mes]} de {anio}"

    # Descripcion base
    info['descripcion_principal'] = f'{descripcion}'

    # Detectar mora
    if hasattr(transaccion, 'mora_aplicada') and transaccion.mora_aplicada:
        info['tiene_mora'] = True
        info['descripcion_principal'] += "(incluye recargo por mora)"
        info['detalles_adicionales'].append({
            'tipo': 'mora',
            'descripcion': f"Recargo por mora: Q.{float(transaccion.mora_monto or 0):,.2f}"
        })

    # Detectar excedentes aplicados
    if hasattr(transaccion, 'excedentes_aplicados') and transaccion.excedentes_aplicados > 0:
        info['tiene_excedentes_aplicados'] = True
        info['descripcion_principal'] += f" - Excedentes aplicados: Q.{transaccion.excedentes_aplicados:.2f}"
        info['detalles_adicionales'].append({
            'tipo': 'excedentes_aplicados',
            'descripcion': f"Se aplicaron Q.{transaccion.excedentes_aplicados:.2f} de pagos anteriores"
        })

    # Detectar excedente generado
    if transaccion.excedente > 0:
        info['tiene_excedente'] = True
        info['seccion_excedente'] = {
            'monto': float(transaccion.excedente),
            'estado': transaccion.estado,
            'descripcion_estado': _get_descripcion_estado_excedente(transaccion.estado)
        }
        
        # Nota especial según el estado
        if transaccion.estado == 'espera_acreditacion':
            info['estado_especial'] = 'espera_acreditacion'
            info['notas_especiales'].append(
                "Este excedente se aplicará automáticamente a futuros pagos una vez acreditado."
            )
        elif transaccion.estado == 'exitosa':
            info['estado_especial'] = 'excedente_disponible'
            info['notas_especiales'].append(
                "Este excedente está disponible para aplicar a futuros pagos."
            )
    
    # Detectar faltante (para casos de complemento)
    if transaccion.faltante > 0:
        info['detalles_adicionales'].append({
            'tipo': 'faltante_cubierto',
            'descripcion': f"Faltante que se cubrió: Q.{float(transaccion.faltante):,.2f}"
        })
    
    return info


def _get_descripcion_estado_excedente(estado):
    """
    Retorna descripcion legible del estado para excedente
    """
    descripciones = {
        'espera_acreditacion': 'Pendiente de acreditación',
        'exitosa': 'Disponible ppara uso',
        'espera_confirmacion': 'En proceso de confirmación'
    }

    return descripciones.get(estado, 'Estado no definido')


def generar_tabla_detalle_transaccion(transaccion, info_analizada):
    """
    Genera los datos para la tabla de detalle en el PDF

    Args: 
        - transaccion: instancia de transaccion
        - info_analizada: dict retornado por analizar_transaccion_recibo

    Returns:
        - list de listas para crear tabla en ReportLab
    """
    tabla_datos = [
        ['CANT.', 'DESCRIPCIÓN', 'MONTO UNITARIO', 'TOTAL']
    ]

    monto_cuota_real = float(transaccion.monto) - float(transaccion.excedente)
    total_acumulado = monto_cuota_real

    # linea principal del pago (solo lo que cubre la cuota)
    tabla_datos.append([
        '1', 
        info_analizada['descripcion_principal'],
        f'Q.{monto_cuota_real:,.2f}',
        f'Q.{total_acumulado:,.2f}'
    ])

    # Linea de excedente si aplica
    if info_analizada['tiene_excedente']:
        total_acumulado += float(transaccion.excedente)
        tabla_datos.append([
            '1',
            f'Excedente generado',
            f'Q.{float(transaccion.excedente):,.2f}',
            f'Q.{total_acumulado:,.2f}'
        ])

    # Lineas de separacion y totales
    tabla_datos.extend([
        ['', '', '', ''],
        ['', '', 'TOTAL PROCESADO:', f'Q.{float(transaccion.monto):,.2f}']
    ])

    return tabla_datos


def generar_seccion_excedente_html(info_excedente):
    """
    Generar HTML para la seccion de excedente en el PDF
    Args:
        info_excedente: dict con informacion del excedente

    Returns:
        str con HTML formateado
    """

    if not info_excedente:
        return ""
    
    html = f"""
    <div style="background-color: #e8f5e8; padding: 15px; border-radius: 8px; border-left: 4px solid #28a745; margin: 15px 0;">
        <b style="color: #155724;">EXCEDENTE GENERADO</b><br/>
        <b>Monto del excedente:</b> Q.{info_excedente['monto']:,.2f}<br/>
        <b>Estado:</b> {info_excedente['descripcion_estado']}<br/>
        <i style="color: #6c757d;">Este monto se aplicará automáticamente a pagos futuros</i>
    </div>
    """

    return html

def generar_observaciones_especiales(info_analizada):
    """
    Genera lista de observaciones especiales para el recibo
    Args: 
        - info analizada: dict retornado por analizar_transaccion_recibo
    Returns:
        - list de strings con observaciones
    """

    observaciones = []

    # Observaciones por mora
    if info_analizada['tiene_mora']:
        observaciones.append("Se aplico recargo por mora segun las condiciones del contrato.")

    # Observaciones por excedentes aplicados
    if info_analizada['tiene_excedentes_aplicados']:
        observaciones.append("Se utilizaron excedentes de pagos anteriores para cubrir parte del monto.")

    # Observaciones por excedentes generados
    if info_analizada['tiene_excedente']:
        if info_analizada['estado_especial']  == 'espera_acreditacion':
            observaciones.append("El excedente generado está pendiente de acreditación y se aplicará automáticamente.")
        elif info_analizada['estado_especial'] == 'excedente_disponible':
            observaciones.append("El excedente esta disponible para aplicar en futuros pagos.")

    # Anadir notas especiales para el analisis
    observaciones.extend(info_analizada['notas_especiales'])

    return observaciones


def es_transaccion_con_excedente(transaccion):
    """
    Verifica si una transaccion tiene excedente que debe reflejarse en el recibo

    Args:
        transaccion: Instancia de transaccion

    Returns:
        Bool
    """

    return (transaccion.excedente > 0 and
            transaccion.estado in ['espera_acreditacion', 'exitosa'])


def obtener_tipo_recibo(transaccion):
    """
    Determina el tipo de recibo segun las caracteristicas de la transaccion

    Args:
        transaccion: Instancia de transaccion

    Returns:
        str: 'normal', 'con_excedente', 'complementaria', 'con_mora'
    """

    if transaccion.excedente > 0:
        return 'con_excedente'
    elif hasattr(transaccion, 'mora_aplicada') and transaccion.mora_aplicada:
        return 'con_mora'
    elif transaccion.faltante > 0:
        return 'complementario'
    else:
        return 'normal'