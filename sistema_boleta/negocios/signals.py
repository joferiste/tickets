from .models import Negocio
from django.dispatch import receiver
from historiales.models import HistorialNegocio
from django.db.models.signals import pre_save, post_save

# ============================================
# HISTORIAL NEGOCIO
# ============================================

_negocio_anterior = {}

@receiver(pre_save, sender=Negocio)
def capturar_negocio_anterior(sender, instance, **kwargs):
    """Captura el estado anterior del negocio antes de guardar"""
    if instance.pk:
        try:
            anterior = Negocio.objects.get(pk=instance.pk)
            _negocio_anterior[instance.pk] = {
                'nombre': anterior.nombre,
                'email': anterior.email,
                'telefono1': anterior.telefono1,
                'telefono2': anterior.telefono2,
                'nit': anterior.nit,
                'estado': anterior.estado.nombre if anterior.estado else None,
                'categoria': anterior.categoria.nombre if anterior.categoria else None,
            }
        except Negocio.DoesNotExist:
            pass

@receiver(post_save, sender=Negocio)
def registrar_historial_negocio(sender, instance, created, **kwargs):
    """Registra cambios en el historial del negocio"""
    
    if created:
        HistorialNegocio.objects.create(
            negocio=instance,
            accion='CREACION',
            tipoCambio='creacion',
            descripcion=f"Negocio creado: {instance.nombre}",
            estadoNuevo=instance.estado.nombre if instance.estado else None
        )
        return
    
    # Obtener estado anterior
    anterior = _negocio_anterior.get(instance.pk)
    if not anterior:
        return
    
    cambios = []
    estado_nuevo = instance.estado.nombre if instance.estado else None
    
    # Detectar cambios
    if anterior['nombre'] != instance.nombre:
        cambios.append(f"Nombre: {anterior['nombre']} → {instance.nombre}")
    
    if anterior['email'] != instance.email:
        cambios.append(f"Email: {anterior['email']} → {instance.email}")
    
    if anterior['telefono1'] != instance.telefono1:
        cambios.append(f"Teléfono: {anterior['telefono1']} → {instance.telefono1}")
    
    if anterior['nit'] != instance.nit:
        cambios.append(f"NIT: {anterior['nit'] or 'Sin NIT'} → {instance.nit or 'Sin NIT'}")
    
    cambio_estado = anterior['estado'] != estado_nuevo
    cambio_categoria = anterior['categoria'] != (instance.categoria.nombre if instance.categoria else None)
    
    if cambio_estado:
        cambios.append(f"Estado: {anterior['estado']} → {estado_nuevo}")
    
    if cambio_categoria:
        cambios.append(f"Categoría: {anterior['categoria']} → {instance.categoria.nombre}")
    
    # Si no hay cambios, salir
    if not cambios:
        if instance.pk in _negocio_anterior:
            del _negocio_anterior[instance.pk]
        return
    
    # Determinar tipo de cambio
    if cambio_estado:
        accion = 'CAMBIO'
        tipo_cambio = 'cambio_estado'
        descripcion = f"Cambio de estado: {anterior['estado']} → {estado_nuevo}"
        if len(cambios) > 1:
            descripcion += ". " + ". ".join([c for c in cambios if 'Estado:' not in c])
    else:
        accion = 'ACTUALIZACION'
        tipo_cambio = 'actualizacion_datos'
        descripcion = "Actualización de datos: " + ". ".join(cambios)
    
    # Crear registro
    HistorialNegocio.objects.create(
        negocio=instance,
        accion=accion,
        tipoCambio=tipo_cambio,
        descripcion=descripcion,
        estadoAnterior=anterior['estado'],
        estadoNuevo=estado_nuevo
    )
    
    # Limpiar cache
    if instance.pk in _negocio_anterior:
        del _negocio_anterior[instance.pk]
