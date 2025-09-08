from django.db import models

class Banco(models.Model):
    nombre = models.CharField(max_length=100)
    numero_cuenta = models.CharField(max_length=50)
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.numero_cuenta}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["nombre", "numero_cuenta"],
                name="unique_nombre_numero_cuenta"
            )
        ] 

        verbose_name = "Banco"
        verbose_name_plural = "Bancos"
        ordering = ['-fechaCreacion']


class Configuracion(models.Model):
    MORA_CHOICES = [
        (5, "5%"), 
        (10, "10%"),
        (15, "15%"), 
        (20, "20%"),
    ]

    DIAS_SIN_RECARGO_CHOICES = [
        (5, "5 días"),
        (10, "10 días"),
        (15, "15 días"),
        (20, "20 días"),
    ]
    mora_porcentaje = models.IntegerField(choices=MORA_CHOICES, default=5)
    dias_sin_recargo = models.IntegerField(choices=DIAS_SIN_RECARGO_CHOICES, default=5)
    banco_principal = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name="configuraciones")
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Asegurar que solo una configuración este activa
        if self.activo:
            Configuracion.objects.filter(activo=True).update(activo=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Config: {self.mora_porcentaje}% de mora, {self.dias_sin_recargo} dias sin recargo."
    
    class Meta:
        verbose_name = 'Configuracion'
        verbose_name_plural = 'Configuraciones'
        ordering = ['-fechaCreacion']