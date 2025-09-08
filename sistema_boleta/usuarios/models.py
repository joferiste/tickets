from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re

telefono_validator = RegexValidator(r'^(?:\d{8}|\d{4}-\d{4})$',
                                    'Número inválido. Debe contener 8 dígitos o seguir el formato XXXX-XXXX.')

class EstadoUsuario(models.Model):
    idEstadoUsuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=40)

    def __str__(self):
        return self.nombre
        

class Usuario(models.Model):
    idUsuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fechaNacimiento = models.DateField(null=True, blank=True)
    dpi = models.CharField(max_length=15)
    nit = models.CharField(max_length=12, null=True, blank=True)
    direccionCompleta = models.CharField(max_length=100)
    telefono1 = models.CharField(max_length=10, validators=[telefono_validator])
    telefono2 = models.CharField(max_length=10, validators=[telefono_validator], null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    estado = models.ForeignKey(EstadoUsuario, on_delete=models.PROTECT)

    def __str__(self):
        return self.nombre

    class Meta: 
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-fechaCreacion'] 