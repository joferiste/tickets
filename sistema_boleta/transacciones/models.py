from django.db import models
from negocios.models import Negocio
from boletas.models import Boleta

class EstadoTransaccion(models.Model):
    idEstadoTransaccion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
    

class Transaccion(models.Model):
    idTransaccion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=120, editable=False, unique=True)
    fechaTransaccion = models.DateTimeField(auto_now_add=True)
    negocio = models.ForeignKey(Negocio, on_delete=models.PROTECT)
    boleta = models.OneToOneField(Boleta, on_delete=models.PROTECT, unique=True)
    estado = models.ForeignKey(EstadoTransaccion, on_delete=models.PROTECT)
    comentario = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        fecha_formateada = self.fechaTransaccion.strftime('%Y-%m-%d %H:%M')
        if not self.nombre:
            self.nombre = f"{self.negocio.nombre}_{self.boleta.numeroBoleta}_{fecha_formateada}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Transaccion"
        verbose_name_plural = "Transacciones"
        ordering = ['-fechaTransaccion']