from locales.models import Local, OcupacionLocal
from historiales.models import HistorialLocal
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

# ============================================
# HISTORIAL LOCAL
# ============================================

_local_anterior = {}

@receiver(pre_save, sender=Local)
def capturar_local_anterior(sender, instance, **kwargs):
    """Captura el estado anterior del local antes de guardar"""
    if instance.pk:
        try:
            anterior = Local.objects.get(pk=instance.pk)
            _local_anterior[instance.pk] = {
                'nombre': anterior.nombre,
                'posicionMapa': anterior.posicionMapa,
                'estado': anterior.estado.nombre if anterior.estado else None,
                'nivel': anterior.nivel.nombre if anterior.nivel else None,
                'costo': anterior.nivel.costo if anterior.nivel else None,
            }
        except Local.DoesNotExist:
            pass

@receiver(post_save, sender=Local)
def registrar_historial_local(sender, instance, created, **kwargs):
    """Registra cambios en el historial del local"""
    
    if created:
        HistorialLocal.objects.create(
            local=instance,
            accion='CREACION',
            tipoCambio='creacion',
            descripcion=f"Local creado: {instance.nombre}",
            estadoNuevo=instance.estado.nombre if instance.estado else None
        )
        return
    
    # Obtener estado anterior
    anterior = _local_anterior.get(instance.pk)
    if not anterior:
        return
    
    cambios = []
    estado_nuevo = instance.estado.nombre if instance.estado else None
    costo_nuevo = instance.nivel.costo if instance.nivel else None
    
    # Detectar cambios
    if anterior['nombre'] != instance.nombre:
        cambios.append(f"Nombre: {anterior['nombre']} → {instance.nombre}")
    
    if anterior['posicionMapa'] != instance.posicionMapa:
        cambios.append(f"Posición: {anterior['posicionMapa'] or 'Sin posición'} → {instance.posicionMapa or 'Sin posición'}")
    
    cambio_estado = anterior['estado'] != estado_nuevo
    cambio_nivel = anterior['nivel'] != (instance.nivel.nombre if instance.nivel else None)
    cambio_costo = anterior['costo'] != costo_nuevo
    
    if cambio_estado:
        cambios.append(f"Estado: {anterior['estado']} → {estado_nuevo}")
    
    if cambio_nivel:
        cambios.append(f"Nivel: {anterior['nivel']} → {instance.nivel.nombre}")
    
    if cambio_costo:
        cambios.append(f"Costo: Q{anterior['costo']} → Q{costo_nuevo}")
    
    # Si no hay cambios, salir
    if not cambios:
        if instance.pk in _local_anterior:
            del _local_anterior[instance.pk]
        return
    
    # Determinar tipo de cambio
    if cambio_estado:
        accion = 'CAMBIO'
        tipo_cambio = 'cambio_estado'
        descripcion = f"Cambio de estado: {anterior['estado']} → {estado_nuevo}"
        if len(cambios) > 1:
            descripcion += ". " + ". ".join([c for c in cambios if 'Estado:' not in c])
    elif cambio_nivel or cambio_costo:
        accion = 'CAMBIO'
        tipo_cambio = 'cambio_nivel_costo'
        descripcion = "Cambio de nivel/costo: " + ". ".join(cambios)
    else:
        accion = 'ACTUALIZACION'
        tipo_cambio = 'actualizacion_datos'
        descripcion = "Actualización de datos: " + ". ".join(cambios)
    
    # Crear registro
    HistorialLocal.objects.create(
        local=instance,
        accion=accion,
        tipoCambio=tipo_cambio,
        descripcion=descripcion,
        estadoAnterior=anterior['estado'],
        estadoNuevo=estado_nuevo
    )
    
    # Limpiar cache
    if instance.pk in _local_anterior:
        del _local_anterior[instance.pk]


# ============================================
# HISTORIAL OCUPACIÓN (Bonus simple)
# ============================================

@receiver(post_save, sender=OcupacionLocal)
def registrar_ocupacion_en_historial(sender, instance, created, **kwargs):
    """Registra cuando un local es ocupado o desocupado"""
    
    if created:
        # Local ocupado
        HistorialLocal.objects.create(
            local=instance.local,
            accion='CAMBIO',
            tipoCambio='ocupacion',
            descripcion=f"Local ocupado por: {instance.negocio.nombre}",
            estadoAnterior='Disponible',
            estadoNuevo='Ocupado'
        )
    else:
        # Si se actualiza fecha_fin, el local se desocupó
        if instance.fecha_fin:
            HistorialLocal.objects.create(
                local=instance.local,
                accion='CAMBIO',
                tipoCambio='desocupacion',
                descripcion=f"Local desocupado (anteriormente: {instance.negocio.nombre})",
                estadoAnterior='Ocupado',
                estadoNuevo='Disponible'
            )