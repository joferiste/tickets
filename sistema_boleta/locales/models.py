from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from negocios.models import Negocio
from decimal import Decimal
from django.utils import timezone


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
    posicionMapa = models.PositiveSmallIntegerField(null=True, blank=True, unique=True, help_text="Número de posición en el mapa visual (1 a 8)")
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    nivel = models.ForeignKey(Nivel, on_delete=models.CASCADE)
    estado = models.ForeignKey(EstadoLocal, on_delete=models.PROTECT)

    def __str__(self):
        return self.nombre
    
    @property
    def costo(self):
        return self.nivel.costo
    
    @property
    def ubicacion(self):
        return self.nivel.ubicacion
    
    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locales"
        ordering = ['-fechaCreacion'] 



class OcupacionLocal(models.Model):
    idOcupacion = models.AutoField(primary_key=True)
    local = models.ForeignKey(Local, on_delete=models.CASCADE, related_name='ocupaciones')
    negocio = models.ForeignKey(Negocio, on_delete=models.PROTECT)
    fecha_asignacion = models.DateField(auto_now_add=True)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.local.nombre} - {self.negocio.nombre} ({self.fecha_inicio} a {self.fecha_fin or 'Actual'})"
    
    class Meta:
        verbose_name = "OcupacionLocal"
        verbose_name_plural = "OcupacionLocales"
        ordering = ['-idOcupacion'] 