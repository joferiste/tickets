from django.db import models
from negocios.models import Negocio

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
    idBoleta = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, editable=False) # Generado automaticamente
    email = models.EmailField(null=False, blank=False)
    fechaIngreso = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='boletas/')
    mensajeCorreo = models.TextField()
    monto = models.CharField(max_length=10)
    numeroBoleta = models.CharField(max_length=20)
    numeroDeCuenta = models.CharField(max_length=20)
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