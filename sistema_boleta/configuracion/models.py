from django.db import models
from decimal import Decimal

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
        (0, "Sin mora"),
        (5, "5%"), 
        (10, "10%"),
        (15, "15%"), 
        (20, "20%"),
    ]
    DIAS_SIN_RECARGO_CHOICES = [
        (0, "Sin días sin recargo"),
        (5, "5 días"),
        (10, "10 días"),
        (15, "15 días"),
        (20, "20 días"),
    ]
    DIAS_CONFIRMACION_CHOICES = [
        (3, "3 días"),
        (5, "5 días"),
        (8, "8 días"),
    ]

    mora_porcentaje = models.IntegerField(choices=MORA_CHOICES, default=0, help_text="Porcentaje de mora a aplicar. 0% = Sin mora automática")
    dias_sin_recargo = models.IntegerField(choices=DIAS_SIN_RECARGO_CHOICES, default=5, help_text="Días sin recargo antes de aplicar mora. Sólo aplica si hay mmora configurada.")
    dias_confirmacion_bancaria = models.IntegerField(choices=DIAS_CONFIRMACION_CHOICES, default=3, help_text="Días para confirmar depósitos bancarios.")
    banco_principal = models.ForeignKey(Banco, on_delete=models.CASCADE, related_name="configuraciones")
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # Asegurar que solo una configuración este activa
        if self.activo:
            Configuracion.objects.filter(activo=True).update(activo=False)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.mora_porcentaje == 0:
            return "Config: Sin mora automática"
        return f"Config: {self.mora_porcentaje}% de mora, {self.dias_sin_recargo} dias sin recargo."
        
    class Meta:
        verbose_name = 'Configuracion'
        verbose_name_plural = 'Configuraciones'
        ordering = ['-fechaCreacion']