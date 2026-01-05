from django.db import models
from negocios.models import Negocio
from configuracion.models import Banco


class BoletaSandbox(models.Model):
    ESTADOS_VALIDACION = [
        ('exitosa', 'Exitosa'),
        ('rechazada', 'Rechazada'),
        ('pendiente', 'Pendiente'),
        ('duplicada', 'Posible Duplicado'),
        ('procesada', 'Procesada'),
        ('sin_imagen', 'Sin Imagen')
    ] 
    remitente = models.EmailField()
    asunto = models.CharField(max_length=255, blank=True)
    mensaje = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='sandbox_boletas/', blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)
    es_valida = models.BooleanField(default=False)
    motivo_rechazo = models.TextField(blank=True, null=True)
    procesado = models.BooleanField(default=False)
    estado_validacion = models.CharField(max_length=30, choices=ESTADOS_VALIDACION, default='pendiente')
    comentarios_validacion = models.CharField(max_length=355)
    leido = models.BooleanField(default=False)
    fecha_eliminacion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de eliminacion programada")

    # Para validaciones
    message_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    hash_image = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    # Definir fecha cuando pasa validaciones y se convierte en boleta
    fecha_procesada = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # Evita que haya dos boletas con el mismo message_id
            models.UniqueConstraint(
                fields=["message_id"],
                name="unique_message_id"
            ),
            # Evita que un mismo remitente suba exactamente la misma imagen
            models.UniqueConstraint(
                fields=["remitente", "hash_image"],
                name="unique_remitente_hash"
            ),
        ]

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
    banco = models.ForeignKey(Banco, on_delete=models.PROTECT)
    origen = models.CharField(max_length=10, choices=origen_choices, default='email')
    estado = models.ForeignKey(EstadoBoleta, on_delete=models.CASCADE)
    tipoPago = models.ForeignKey(TipoPago, on_delete=models.PROTECT)
    negocio = models.ForeignKey(Negocio, on_delete=models.PROTECT)
    es_complemetaria = models.BooleanField(default=False)
    fechaDeposito = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):    
        # Asignar estado por defecto si no viene
        if not self.estado_id:
            self.estado = EstadoBoleta.objects.get(nombre='Pendiente')

        # Asignar tipo de pago por defecto si no viene
        if not self.tipoPago_id:
            self.tipoPago = TipoPago.objects.get(nombre='Por definir')

        super().save(*args, **kwargs)

    def __str__(self):  
        return f"{self.nombre}"
    
    class Meta:
        verbose_name = "Boleta"
        verbose_name_plural = "Boletas"
        ordering = ['-fechaIngreso'] 
        constraints = [
            models.UniqueConstraint(fields=["banco", "numeroBoleta"], name="unique_banco_boleta")
        ]