from django.db import models
from negocios.models import Negocio


class BoletaSandbox(models.Model):
    remitente = models.EmailField()
    asunto = models.CharField(max_length=255, blank=True)
    mensaje = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='sandbox_boletas/', blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    es_valida = models.BooleanField(default=False)
    motivo_rechazo = models.TextField(blank=True, null=True)
    procesado = models.BooleanField(default=False)
    estado_validacion = models.CharField(max_length=30)
    comentarios_validacion = models.CharField(max_length=355)
    leido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.remitente} - {self.fecha_recepcion.strftime('%Y-%m-%d %H:%M')}"

class EstadoBoleta(models.Model):
    idEstadoBoleta = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)

    def __str__(self):
        return self.nombre


class TipoPago(models.Model):
    idTipoPago = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)

    def __str__(self):
        return self.nombre
    
    
class Boleta(models.Model):

    origen_choices = (
        ('email', 'Correo electrónico'),
        ('manual', 'Carga Manual'),
    )

    idBoleta = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, editable=False) # Generado automaticamente
    email = models.EmailField(null=False, blank=False)
    asunto = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(blank=True, null=True)
    fechaIngreso = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='boletas/')
    mensajeCorreo = models.TextField()
    monto = models.CharField(max_length=10)
    numeroBoleta = models.CharField(max_length=20)
    numeroDeCuenta = models.CharField(max_length=20)
    origen = models.CharField(max_length=10, choices=origen_choices, default='email')
    estado = models.ForeignKey(EstadoBoleta, on_delete=models.CASCADE)
    tipoPago = models.ForeignKey(TipoPago, on_delete=models.PROTECT)
    negocio = models.ForeignKey(Negocio, on_delete=models.PROTECT)

    def save(self, *args, **kwargs):    
        # Asignar estado por defecto si no viene
        if not self.estado_id:
            self.estado = EstadoBoleta.objects.get(nombre='Pendiente')

        # Asignar tipo de pago por defecto si no viene
        if not self.tipoPago_id:
            self.tipoPago = TipoPago.objects.get(nombre='Por definir')

        fecha_formateada = self.fechaIngreso.strftime('%Y-%m-%d %H:%M')
        if self.negocio and self.numeroBoleta:
            self.nombre = f"{self.negocio.nombre} - {self.numeroBoleta} - {fecha_formateada}"
        else:
            # Si no existe numero de boleta, se usa el email.
            self.nombre = f"{self.email} - {fecha_formateada}"
        super().save(*args, **kwargs)

    def __str__(self):  
        return self.nombre
    
    class Meta:
        verbose_name = "Boleta"
        verbose_name_plural = "Boletas"
        ordering = ['-fechaIngreso'] 