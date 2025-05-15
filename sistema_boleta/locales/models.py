from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from negocios.models import Negocio
from decimal import Decimal


class Ubicacion(models.Model):
    idUbicacion = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre
    

class Nivel(models.Model):
    idNivel = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30)
    costo = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nombre} - {self.ubicacion.nombre}"

    
class EstadoLocal(models.Model):
    idEstado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)

    def __str__(self):
        return self.nombre


class Local(models.Model):
    idLocal = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.CASCADE)
    nivel = models.ForeignKey(Nivel, on_delete=models.CASCADE)
    negocio = models.ForeignKey(Negocio, on_delete=models.PROTECT)
    estado = models.ForeignKey(EstadoLocal, on_delete=models.PROTECT)

    def __str__(self):
        return self.nombre
    
    @property
    def costo(self):
        return self.nivel.costo
    
    def clean(self):
        if self.nivel.ubicacion != self.ubicacion:
            raise ValidationError("El nivel seleccionado no pertenece a la ubicacion indicada")
    
    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locales"
        ordering = ['-fechaCreacion']