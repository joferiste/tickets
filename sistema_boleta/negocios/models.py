from django.db import models
from django.core.validators import RegexValidator
from usuarios.models import Usuario

telefono_validator = RegexValidator(r'^(?:\d{8}|\d{4}-\d{4})$',
                                    'Número inválido. Debe contener 8 dígitos o seguir el formato XXXX-XXXX.')

class EstadoNegocio(models.Model):
    idEstadoNegocio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30)

    def __str__(self):
        return self.nombre

class Categoria(models.Model):
    idCategoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)    

    def __str__(self):
        return self.nombre

class Negocio(models.Model):
    idNegocio = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True, null=False, blank=False)
    telefono1 = models.CharField(max_length=10, validators=[telefono_validator])
    telefono2 = models.CharField(max_length=10, validators=[telefono_validator], null=True, blank=True)
    nit = models.CharField(max_length=20, null=True, blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    estado = models.ForeignKey(EstadoNegocio, on_delete=models.PROTECT)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self): 
        return self.nombre 

    class Meta:
        verbose_name = "Negocio"
        verbose_name_plural = "Negocios"
        ordering = ['-fechaCreacion']
