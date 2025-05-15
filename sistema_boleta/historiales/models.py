from django.db import models
from negocios.models import Negocio
from locales.models import Local
from transacciones.models import Transaccion
import uuid

class HistorialBase(models.Model):
    fechaModificacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    accion = models.CharField(max_length=20, choices=[('CREACION', 'creación'), ('ACTUALIZACION', 'actualización'), ('ELIMINACION', 'eliminación'), ('CAMBIO', 'cambio'),])
    tipoCambio = models.CharField(max_length=50)
    estadoAnterior = models.CharField(max_length=15, null=True, blank=True)
    estadoNuevo = models.CharField(max_length=15, null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ['-fechaModificacion']


class HistorialNegocio(HistorialBase):
    idHistorialNegocio = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    negocio = models.ForeignKey(Negocio, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.negocio.nombre} - {self.accion} en {self.fechaModificacion}"
    


class HistorialLocal(HistorialBase):
    idHistorialLocal = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    local = models.ForeignKey(Local, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.local.nombre} - {self.accion} en {self.fechaModificacion}"
    

class HistorialTransaccion(HistorialBase):
    idHistorialTransaccion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.transaccion.nombre} - {self.accion} en {self.fechaModificacion}"