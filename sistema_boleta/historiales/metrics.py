from django.db.models import Sum, Avg, Count
from dateutil.relativedelta import relativedelta
from .models import PerfilPagoNegocio
from transacciones.models import Transaccion
from collections import defaultdict

def actualizar_metricas_negocio(negocio):
    """
    Recalcula todas las metricas del perfil del negocio
    """
    perfil, created = PerfilPagoNegocio.objects.get_or_create(negocio=negocio)

    transacciones = Transaccion.objects.filter(
        negocio=negocio,
        estado='exitosa'
    ).select_related('boleta', 'boleta__tipoPago').order_by('fechaTransaccion')

    # DEBUG: Ver qué transacciones encuentra
    print(f"\n{'='*50}")
    print(f"NEGOCIO: {negocio.nombre}")
    print(f"Transacciones exitosas encontradas: {transacciones.count()}")
    for t in transacciones:
        print(f"  - ID: {t.idTransaccion}, Monto: {t.monto}, Estado: {t.estado}")
    print(f"{'='*50}\n")
    

    if not transacciones.exists():
        return perfil
    
    # Estadisticas generales
    perfil.total_pagos_realizados = transacciones.count()
    perfil.total_monto_pagado = transacciones.aggregate(Sum('monto'))['monto__sum'] or 0

    perfil.promedio_monto_pago = (
        perfil.total_monto_pagado / perfil.total_pagos_realizados
        if perfil.total_pagos_realizados > 0 else 0
        )

    # Dia promedio
    dias = [t.fechaTransaccion.day for t in transacciones if t.fechaTransaccion]
    if dias:
        perfil.dia_promedio_pago = sum(dias) // len(dias) if dias else None

    # Mes con más pagos
    meses_dict = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    meses_count = {}
    for t in transacciones:
        mes = t.fechaTransaccion.month
        meses_count[mes] = meses_count.get(mes, 0) + 1
    
    if meses_count:
        mes_mas_frecuente = max(meses_count, key=meses_count.get)
        perfil.mes_con_mas_pagos = meses_dict[mes_mas_frecuente]

    
    # ========== MÉTODOS DE PAGO ==========
    perfil.total_pago_efectivo = 0
    perfil.total_pago_cheque = 0
    perfil.total_pago_deposito = 0
    
    print("Analizando metodos de pago:")
    for t in transacciones:
        # Verificar que la boleta existe y tiene tipoPago
        if t.boleta and t.boleta.tipoPago:
            tipo_nombre = t.boleta.tipoPago.nombre
            print(f"    Trans {t.idTransaccion}: Tipo = {tipo_nombre}")

            if tipo_nombre.lower() == "efectivo":
                perfil.total_pago_efectivo += 1
            elif "cheque" in tipo_nombre:
                perfil.total_pago_cheque += 1
            elif "deposito" in tipo_nombre or "deposito" in tipo_nombre:
                perfil.total_pago_deposito += 1
            else:
                # Si llegan otros metodos en el futuro
                print(f"Metodo desconocido: {tipo_nombre}")
        else:
            print(f" Trans {t.idTransaccion} sin boleta o sin tipoPago")

    # Calcular los totales consolidados
    total_efectivo = perfil.total_pago_efectivo
    total_no_efectivo = perfil.total_pago_cheque + perfil.total_pago_deposito
    
    # Determinar método preferido
    metodos = {
        'Efectivo': total_efectivo,
        'No Efectivo': total_no_efectivo,
    }
    
    if any(metodos.values()):
        perfil.metodo_preferido = max(metodos, key=metodos.get)
        perfil.porcentaje_metodo_preferido = (
            metodos[perfil.metodo_preferido] / perfil.total_pagos_realizados
        ) * 100
    else:
        perfil.metodo_preferido = None
        perfil.porcentaje_metodo_preferido = 0


    # Mora 
    perfil.total_veces_con_mora = transacciones.filter(mora_monto__gt=0).count()
    if perfil.total_pagos_realizados > 0:
        pagos_puntuales = perfil.total_pagos_realizados - perfil.total_veces_con_mora
        perfil.porcentaje_puntualidad = (pagos_puntuales / perfil.total_pagos_realizados) * 100

    # Racha sin mora
    racha = 0
    for t in reversed(list(transacciones)):
        if t.mora_monto == 0:
            racha += 1
        else:
            break
    perfil.racha_actual_sin_mora = racha

    # ========== PAGOS PARCIALES Y EXCEDENTES ==========
    perfil.total_pagos_con_faltante = transacciones.filter(faltante__gt=0).count()
    perfil.total_pagos_con_excedente = transacciones.filter(excedente__gt=0).count()
    perfil.total_excedente_acumulado = transacciones.aggregate(Sum('excedente'))['excedente__sum'] or 0
    perfil.total_pagos_completos = perfil.total_pagos_realizados - perfil.total_pagos_con_faltante
    

    # ========== INFORMACIÓN TEMPORAL ==========
    primera_transaccion = transacciones.first()
    ultima_transaccion = transacciones.last()
    
    if primera_transaccion:
        perfil.primer_pago = primera_transaccion.fechaTransaccion.date()
    
    if ultima_transaccion:
        perfil.ultimo_pago = ultima_transaccion.fechaTransaccion.date()
    
    # Calcular meses como cliente
    if perfil.primer_pago and perfil.ultimo_pago:
        delta = relativedelta(perfil.ultimo_pago, perfil.primer_pago)
        perfil.meses_como_cliente = delta.years * 12 + delta.months + 1  # +1 para incluir el mes actual

    perfil.save()
    print(f"GUARDADO: Total pagos={perfil.total_pagos_realizados}, Monto total={perfil.total_monto_pagado:,.2f}")
    print(f"Método preferido: {perfil.metodo_preferido}\n")
    return perfil


def obtener_historial_completo(negocio):
    """
    Obtiene el historial completo de transacciones de un negocio
    
    Args:
        negocio: Instancia de Negocio
    
    Returns:
        dict: Historial organizado por año
    """

    transacciones = Transaccion.objects.filter(
        negocio=negocio,
        estado='exitosa'
    ).select_related('boleta').order_by('-fechaTransaccion')
    
    historial_por_ano = defaultdict(list)
    
    for t in transacciones:
        ano = t.fechaTransaccion.year
        
        # Determinar método de pago
        metodo_pago = 'Desconocido'
        if hasattr(t, 'boleta') and t.boleta:
            if t.boleta.tipoPago == 'Efectivo':
                metodo_pago = 'Efectivo'
            elif t.boleta.tipoPago in ['Cheque Propio', 'Cheque Ajeno', 'Por Definir', 'Cheque Exterior']:
                metodo_pago = t.boleta.tipoBoleta.capitalize()
        
        historial_por_ano[ano].append({
            'id': t.idTransaccion,
            'fecha': t.fechaTransaccion,
            'periodo': t.periodo_pagado,
            'monto': t.monto,
            'metodo': metodo_pago,
            'tuvo_mora': t.mora_monto > 0,
            'monto_mora': t.mora_monto,
            'dias_retraso': t.dias_retraso,
            'tiene_faltante': t.faltante > 0,
            'tiene_excedente': t.excedente > 0,
            'estado': t.estado,
        })
    
    # Ordenar años de más reciente a más antiguo
    return dict(sorted(historial_por_ano.items(), reverse=True))


def obtener_historial_timeline(negocio):
    """
    Retorna historial organizado por anio para timeline
    """

    transacciones = Transaccion.objects.filter(
        negocio=negocio,
        estado='exitosa'
    ).select_related('boleta').order_by('-fechaTransaccion')

    timeline = defaultdict(list)

    for t in transacciones:
        timeline[t.fechaTransaccion.year].append({
            'fecha': t.fechaTransaccion,
            'periodo': t.periodo_pagado,
            'monto': t.monto,
            'metodo': t.boleta.tipoPago if t.boleta else 'Desconocido',
            'tuvo_mora': t.mora_monto > 0,
            'monto_mora': t.mora_monto
        })
    
    return dict(sorted(timeline.items(), reverse=True))