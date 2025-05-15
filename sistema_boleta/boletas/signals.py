from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Boleta


@receiver(post_save, sender=Boleta)
def set_nombre_boleta(sender, instance, created, **kwargs):
    if created:
        fecha_formateada = instance.fechaIngreso.strftime('%Y-%m-%d %H:%M')
        if instance.negocio and instance.numeroBoleta:
            instance.nombre = f"{instance.negocio.nombre} - {instance.numeroBoleta} - {fecha_formateada}"
        else:
            instance.nombre = f"{instance.email} - {fecha_formateada}"
        instance.save()

