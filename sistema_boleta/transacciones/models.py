from django.db import models
from boletas.models import Boleta
from negocios.models import Negocio
from datetime import datetime
from django.utils.text import slugify
from django.utils import timezone
from datetime import datetime
from locales.models import OcupacionLocal
 
class Transaccion(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),     # Recién creada
        ('en_revision', 'En revisión'), # Validación manual o por reglas
        ('espera_confirmacion', 'En espera de confirmación de fondos'),
        ('espera_confirmacion_faltante', 'En espera de confirmación - Con faltante'), 
        ('espera_complemento', 'Espera de complemento de pago'),
        ('espera_acreditacion', 'Espera de acreditación de saldo a favor'),
        ('procesada', 'Procesada'),     # Validaciones técnicas pasadas
        ('exitosa', 'Exitosa'),         # Confirmado, saldo aplicado 
        ('rechazada', 'Rechazada'),      # Invalida (ej, boleta repetida)
        ('fallida', 'Fallida'),         # Intentada pero no se acredito 
    ]
    idTransaccion = models.AutoField(primary_key=True)  
    nombre = models.CharField(max_length=120, editable=False, unique=True) 
    fecha_ingreso_sistema = models.DateTimeField(null=True, blank=True)
    fechaTransaccion = models.DateTimeField(auto_now_add=True) 
    negocio = models.ForeignKey(Negocio, on_delete=models.PROTECT)
    boleta = models.OneToOneField(Boleta, on_delete=models.PROTECT, unique=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=45, choices=ESTADOS, default='pendiente')
    periodo_pagado = models.CharField(max_length=8, help_text="Formato: YYYY-MM")
    comentario = models.TextField(null=True, blank=True)
    ultima_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    mora_monto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    faltante = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    excedente = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dias_retraso = models.IntegerField(default=0) 
    fecha_limite_confirmacion = models.DateTimeField(null=True, blank=True)
    mensaje_final = models.TextField(null=True, blank=True)
    ocupacion = models.ForeignKey(OcupacionLocal, on_delete=models.PROTECT, null=True)

    @property
    def dias_mora_actuales(self):
        """
        Calcula los dias de mora EN TIEMPO REAL desde la fecha de ingreso al sistema.
        Este valor se actualiza automaticamente cada vez que se consulta.
        """
        if not self.fecha_ingreso_sistema:
            return 0
        
        # Obtener fecha actual (sin hora)
        hoy = timezone.now().date()

        # Convertir fecha_ingreso_sistema a date (sin hora)
        fecha_ingreso = self.fecha_ingreso_sistema.date()

        # Calcular diferencia de dias
        dias = (hoy - fecha_ingreso).days

        # Retornar solo si es positivo (no puede ser negativo)
        return max(0, dias)
    
    @property
    def dias_para_limite(self):
        """
        Calcula cuantos dias faltan para la fecha limite de confirmacion
        Retorna numero negativo si ya paso la fecha limite
        """
        if not self.fecha_limite_confirmacion:
            return None
        
        hoy = timezone.now()
        diferencia = (self.fecha_limite_confirmacion - hoy).days

        return diferencia
    
    @property
    def esta_en_mora(self):
        """
        Verifica si la transaccion esta en mora (paso la fecha limite)
        """
        if not self.fecha_limite_confirmacion:
            return False
        
        return timezone.now() > self.fecha_limite_confirmacion
    
    @property
    def calcular_mora_monto(self, monto_por_dia=400):
        """
        Calcular el monto de mora basado en los dias actuales de mora.
        Puedes llamar esto cuando necesitas actualizar el monto.
        """
        return self.dias_mora_actuales * monto_por_dia

    def save(self, *args, **kwargs):
        if not self.nombre and self.boleta_id:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            negocio_slug = slugify(self.negocio.nombre)
            self.nombre = f"TRANSACCION-{self.boleta_id}-{negocio_slug}-{timestamp}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.negocio.nombre}"
    
    class Meta:
        verbose_name = "Transaccion"
        verbose_name_plural = "Transacciones"
        ordering = ['-fechaTransaccion'] 

