from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from transacciones.models import Transaccion
from historiales.models import HistorialTransaccion


# Variable temporal para guardar el estado anterior completo
_transaccion_anterior = {}


@receiver(pre_save, sender=Transaccion)
def guardar_estado_anterior(sender, instance, **kwargs):
    """
    Antes de guardar, captura el estado anterior completo de la transacción
    para poder detectar todos los cambios.
    """
    if instance.pk:  # Solo si ya existe (actualización)
        try:
            anterior = Transaccion.objects.get(pk=instance.pk)
            
            # Obtener método de pago anterior
            try:
                metodo_pago_anterior = anterior.boleta.tipoPago.nombre if hasattr(anterior.boleta, 'tipoPago') else 'Efectivo'
            except:
                metodo_pago_anterior = 'Efectivo'
            
            _transaccion_anterior[instance.pk] = {
                'estado': anterior.estado,
                'monto': anterior.monto,
                'comentario': anterior.comentario,
                'mensaje_final': anterior.mensaje_final,
                'metodo_pago': metodo_pago_anterior,  # Guardar método de pago anterior
                'mora_monto': anterior.mora_monto,
                'faltante': anterior.faltante,
                'excedente': anterior.excedente,
                'dias_retraso': anterior.dias_retraso,
            }
        except Transaccion.DoesNotExist:
            pass


@receiver(post_save, sender=Transaccion)
def crear_historial_transaccion(sender, instance, created, **kwargs):
    """
    Después de guardar una transacción, crea el registro en HistorialTransaccion.
    
    REGLAS DE TRAZABILIDAD:
    1. CREACION: Registra estado inicial completo (incluye método de pago)
    2. CAMBIO DE ESTADO: Registra cambio con datos actualizados
    3. ACTUALIZACIÓN DE DATOS: Registra cambios en comentarios, mensajes, montos, método de pago
    4. TRAZABILIDAD COMPLETA: Mantiene historial de todos los campos importantes
    """
    
    # Obtener método de pago actual desde la boleta
    try:
        metodo_pago = instance.boleta.tipoPago.nombre if hasattr(instance.boleta, 'tipoPago') else 'Efectivo'
    except:
        metodo_pago = 'Efectivo'
    
    # CASO 1: CREACIÓN (primera vez)
    if created:
        HistorialTransaccion.objects.create(
            transaccion=instance,
            fechaModificacion=timezone.now(),
            descripcion=f"Transacción creada: {instance.nombre}. Estado inicial: {instance.estado}. Método de pago: {metodo_pago}",
            accion='CREACION',
            tipoCambio='creacion_transaccion',
            estadoAnterior=None,
            estadoNuevo=instance.estado,
            monto=instance.monto,
            metodo_pago=metodo_pago,
            periodo_pagado=instance.periodo_pagado,
            monto_mora=instance.mora_monto,
            dias_retraso=instance.dias_retraso,
            observaciones=f"CREACIÓN INICIAL:\n"
                         f"  Estado: {instance.estado}\n"
                         f"  Método de pago: {metodo_pago}\n"
                         f"  Monto: Q{instance.monto}\n"
                         f"  Comentario: {instance.comentario or '[sin comentarios]'}\n"
                         f"  Mensaje: {instance.mensaje_final or '[sin mensaje]'}"
        )
        return
    
    # CASO 2: ACTUALIZACIÓN (ya existe)
    anterior = _transaccion_anterior.get(instance.pk, {})
    
    # Si no hay datos anteriores, salir
    if not anterior:
        return
    
    # Detectar qué cambió
    cambios = []
    estado_anterior = anterior.get('estado')
    estado_nuevo = instance.estado
    metodo_pago_anterior = anterior.get('metodo_pago')
    
    cambio_estado = estado_anterior != estado_nuevo
    cambio_comentario = anterior.get('comentario') != instance.comentario
    cambio_mensaje = anterior.get('mensaje_final') != instance.mensaje_final
    cambio_metodo_pago = metodo_pago_anterior != metodo_pago
    cambio_monto = anterior.get('monto') != instance.monto
    cambio_mora = anterior.get('mora_monto') != instance.mora_monto
    cambio_faltante = anterior.get('faltante') != instance.faltante
    cambio_excedente = anterior.get('excedente') != instance.excedente
    cambio_dias_retraso = anterior.get('dias_retraso') != instance.dias_retraso
    
    # REGLA CLAVE: Si hay cambio de estado, los cambios de comentario/mensaje
    # se incluyen en ese mismo registro de CAMBIO, NO se crea registro separado
    # Esto mantiene la traza limpia: 1 cambio de estado = 1 registro
    if cambio_estado:
        # Todos los cambios se registran, pero NO como cambios separados
        # Solo se usa para la descripción y observaciones
        pass
    
    # Construir descripción de cambios
    if cambio_estado:
        cambios.append(f"Estado: {estado_anterior} → {estado_nuevo}")
    if cambio_metodo_pago:
        cambios.append(f"Método de pago: {metodo_pago_anterior} → {metodo_pago}")
    if cambio_monto:
        cambios.append(f"Monto: Q{anterior.get('monto')} → Q{instance.monto}")
    if cambio_mora:
        cambios.append(f"Mora: Q{anterior.get('mora_monto')} → Q{instance.mora_monto}")
    if cambio_faltante:
        cambios.append(f"Faltante: Q{anterior.get('faltante')} → Q{instance.faltante}")
    if cambio_excedente:
        cambios.append(f"Excedente: Q{anterior.get('excedente')} → Q{instance.excedente}")
    if cambio_dias_retraso:
        cambios.append(f"Días retraso: {anterior.get('dias_retraso')} → {instance.dias_retraso}")
        
    # Si no hay cambios relevantes, no crear historial
    if not cambios:
        if instance.pk in _transaccion_anterior:
            del _transaccion_anterior[instance.pk]
        return
    
    # Determinar tipo de cambio y acción
    if cambio_estado:
        accion = 'CAMBIO'
        tipo_cambio = 'cambio_estado'
        descripcion = f"Cambio de estado: {estado_anterior} → {estado_nuevo}"
        
        # Agregar información adicional relevante al cambio de estado
        info_adicional = []
        if cambio_metodo_pago:
            info_adicional.append(f"Método de pago: {metodo_pago_anterior} → {metodo_pago}")
        if cambio_faltante:
            info_adicional.append(f"Faltante: Q{anterior.get('faltante')} → Q{instance.faltante}")
        if cambio_excedente:
            info_adicional.append(f"Excedente: Q{anterior.get('excedente')} → Q{instance.excedente}")
        if cambio_mora:
            info_adicional.append(f"Mora: Q{anterior.get('mora_monto')} → Q{instance.mora_monto}")
        
        if info_adicional:
            descripcion += ". " + ". ".join(info_adicional)
            
    elif cambio_metodo_pago:
        accion = 'ACTUALIZACION'
        tipo_cambio = 'cambio_metodo_pago'
        descripcion = f"Cambio de método de pago: {metodo_pago_anterior} → {metodo_pago}"
    elif cambio_comentario or cambio_mensaje:
        # Solo llega aquí si NO hubo cambio de estado
        accion = 'ACTUALIZACION'
        tipo_cambio = 'actualizacion_seguimiento'
        descripcion = "Actualización de seguimiento: " + ", ".join(cambios)
    elif cambio_monto or cambio_mora or cambio_faltante or cambio_excedente:
        accion = 'ACTUALIZACION'
        tipo_cambio = 'actualizacion_montos'
        descripcion = "Actualización de montos: " + ", ".join(cambios)
    else:
        accion = 'ACTUALIZACION'
        tipo_cambio = 'actualizacion_datos'
        descripcion = "Actualización de datos: " + ", ".join(cambios)
    
    # Construir observaciones detalladas con trazabilidad completa
    observaciones_partes = []
    
    # Cambios generales
    observaciones_partes.append("CAMBIOS:\n" + "\n".join([f"  • {c}" for c in cambios]))
    
    # Trazabilidad de método de pago
    if cambio_metodo_pago:
        observaciones_partes.append(
            f"\nMÉTODO DE PAGO:\n"
            f"  Anterior: {metodo_pago_anterior}\n"
            f"  Nuevo: {metodo_pago}"
        )
    
    # Trazabilidad de comentarios (SIEMPRE mostrar si cambió)
    if cambio_comentario:
        observaciones_partes.append(
            f"\nCOMENTARIO:\n"
            f"  Anterior: {anterior.get('comentario') or '[vacío]'}\n\n"
            f"  Nuevo: {instance.comentario or '[vacío]'}\n"
        )
    
    # Trazabilidad de mensajes (SIEMPRE mostrar si cambió)
    if cambio_mensaje:
        observaciones_partes.append(
            f"\nMENSAJE FINAL:\n"
            f"  Anterior: {anterior.get('mensaje_final') or '[vacío]'}\n\n"
            f"  Nuevo: {instance.mensaje_final or '[vacío]'}"
        )
    
    # Estado actual (si no hubo cambios en comentario/mensaje/metodo_pago)
    if not cambio_comentario and not cambio_mensaje and not cambio_metodo_pago:
        observaciones_partes.append(
            f"\nESTADO ACTUAL:\n"
            f"  Método de pago: {metodo_pago}\n"
            f"  Comentario: {instance.comentario or '[sin comentarios]'}\n"
            f"  Mensaje: {instance.mensaje_final or '[sin mensaje]'}"
        )
    
    observaciones_completas = "\n".join(observaciones_partes)
    
    # Crear el registro de historial
    HistorialTransaccion.objects.create(
        transaccion=instance,
        fechaModificacion=timezone.now(),
        descripcion=descripcion,
        accion=accion,
        tipoCambio=tipo_cambio,
        estadoAnterior=estado_anterior,
        estadoNuevo=estado_nuevo,
        monto=instance.monto,
        metodo_pago=metodo_pago,  # Guardar método de pago actual
        periodo_pagado=instance.periodo_pagado,
        monto_mora=instance.mora_monto,
        dias_retraso=instance.dias_retraso,
        observaciones=observaciones_completas
    )
    
    # Limpiar el diccionario temporal
    if instance.pk in _transaccion_anterior:
        del _transaccion_anterior[instance.pk]


# Función para consultar historial completo de una transacción
def obtener_historial_completo(transaccion):
    """
    Obtiene el historial completo de una transacción con toda la trazabilidad.
    
    Returns:
        QuerySet ordenado cronológicamente
    """
    return HistorialTransaccion.objects.filter(
        transaccion=transaccion
    ).order_by('fechaModificacion')


# Función para obtener la línea de tiempo de estados
def obtener_linea_tiempo_estados(transaccion):
    """
    Obtiene la línea de tiempo de cambios de estado de una transacción.
    
    Returns:
        list: [
            {
                'fecha': datetime,
                'estado': str,
                'metodo_pago': str,
                'descripcion': str,
                'observaciones': str
            }
        ]
    """
    historial = HistorialTransaccion.objects.filter(
        transaccion=transaccion,
        accion__in=['CREACION', 'CAMBIO']
    ).order_by('fechaModificacion')
    
    linea_tiempo = []
    for h in historial:
        linea_tiempo.append({
            'fecha': h.fechaModificacion,
            'estado': h.estadoNuevo,
            'metodo_pago': h.metodo_pago,
            'descripcion': h.descripcion,
            'observaciones': h.observaciones
        })
    
    return linea_tiempo


# Función auxiliar para crear historial manual
def crear_historial_manual(transaccion, accion='ACTUALIZACION', descripcion=None, observaciones=None):
    """
    Función auxiliar para crear historial manualmente cuando sea necesario.
    
    Args:
        transaccion: Instancia de Transaccion
        accion: 'CREACION', 'ACTUALIZACION', 'CAMBIO', 'ELIMINACION'
        descripcion: Texto descriptivo del cambio
        observaciones: Observaciones detalladas
    """
    if descripcion is None:
        descripcion = f"Registro manual de transacción {transaccion.nombre}"
    
    try:
        metodo_pago = transaccion.boleta.tipoPago.nombre if hasattr(transaccion.boleta, 'tipoPago') else 'Efectivo'
    except:
        metodo_pago = 'Efectivo'
    
    if observaciones is None:
        observaciones = (
            f"Registro manual\n"
            f"Método de pago: {metodo_pago}\n"
            f"Comentario: {transaccion.comentario or '[sin comentarios]'}\n"
            f"Mensaje: {transaccion.mensaje_final or '[sin mensaje]'}"
        )
    
    HistorialTransaccion.objects.create(
        transaccion=transaccion,
        fechaModificacion=timezone.now(),
        descripcion=descripcion,
        accion=accion,
        tipoCambio='registro_manual',
        estadoAnterior=None,
        estadoNuevo=transaccion.estado,
        monto=transaccion.monto,
        metodo_pago=metodo_pago,
        periodo_pagado=transaccion.periodo_pagado,
        monto_mora=transaccion.mora_monto,
        dias_retraso=transaccion.dias_retraso,
        observaciones=observaciones
    )