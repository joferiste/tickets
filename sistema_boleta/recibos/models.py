from django.db import models
from transacciones.models import Transaccion
import uuid

class EstadoRecibo(models.Model):
    idEstadoRecibo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)

    def __str__(self):
        return self.nombre
    

class Recibo(models.Model):
    idRecibo = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    correlativo = models.CharField(max_length=20, null=False, blank=False)
    nombre = models.CharField(max_length=110, editable=False) # Se genera automaticamente
    transaccion = models.OneToOneField(Transaccion, on_delete=models.PROTECT, unique=True)
    email = models.EmailField(null=False, blank=False)
    fechaGeneracion = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='recibos/')
    estado = models.ForeignKey(EstadoRecibo, on_delete=models.PROTECT)
    enviado = models.BooleanField(default=False)
    fechaEnvio = models.DateTimeField(null=True, blank=True)
    mensajeEnvio = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.nombre

     
    def save(self, *args, **kwargs):
        if not self.nombre:
            self.nombre = f"Recibo-{self.transaccion.negocio.nombre}_{self.transaccion.boleta.numeroBoleta}"
        if not self.email:
            self.emailAsociado = self.transaccion.boleta.email
        super().save(*args, **kwargs)


    class Meta:
        verbose_name = 'Recibo'
        verbose_name_plural = 'Recibos'
        ordering = ['-fechaGeneracion']

