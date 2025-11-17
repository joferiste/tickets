from django.db import models
from negocios.models import Negocio
from locales.models import Local
from transacciones.models import Transaccion
import uuid

class HistorialBase(models.Model):
    fechaModificacion = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()
    accion = models.CharField(max_length=25, choices=[('CREACION', 'creación'), ('ACTUALIZACION', 'actualización'), ('ELIMINACION', 'eliminación'), ('CAMBIO', 'cambio'),])
    tipoCambio = models.CharField(max_length=80)
    estadoAnterior = models.CharField(max_length=70, null=True, blank=True)
    estadoNuevo = models.CharField(max_length=70, null=True, blank=True)

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
    transaccion = models.ForeignKey(Transaccion, on_delete=models.CASCADE, related_name='historial')
    
    # Datos especificos para analisis
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=50)
    periodo_pagado = models.CharField(max_length=7) #YYYY-MM
    monto_mora = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    dias_retraso = models.IntegerField(default=0)

    # Auditoria
    # usuario_responsable = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-fechaModificacion']
        verbose_name = "Historial de Transaccion"
        verbose_name_plural = "Historiales de Transacciones"
        indexes = [
            models.Index(fields=['transaccion', '-fechaModificacion']),
            models.Index(fields=['periodo_pagado']),
            models.Index(fields=['metodo_pago']),
        ]

    def __str__(self):
        return f"{self.transaccion.negocio.nombre} - {self.periodo_pagado} - {self.accion}" 
    

class PerfilPagoNegocio(models.Model):
    """
    Metricas agregadas del comportamiento de pago de un negocio
    """

    negocio = models.OneToOneField(Negocio, on_delete=models.CASCADE, related_name='perfil_pago')

    # Estadisticas generales
    total_pagos_realizados = models.IntegerField(default=0)
    total_monto_pagado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    promedio_monto_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Patrones de pago
    dia_promedio_pago = models.IntegerField(
        null=True,
        blank=True,
        help_text="Día promedio del mes en que realiza el pago (1-31)"
    )
    mes_con_mas_pagos = models.CharField(max_length=20, null=True, blank=True)

    # Metodos de pago
    total_pago_efectivo = models.IntegerField(default=0)
    total_pago_cheque = models.IntegerField(default=0)
    total_pago_deposito = models.IntegerField(default=0)
    metodo_preferido = models.CharField(max_length=50, null=True, blank=True)
    porcentaje_metodo_preferido = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Analisis de mora
    total_veces_con_mora = models.IntegerField(default=0)
    total_mora_pagada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    promedio_dias_retraso = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    porcentaje_puntualidad = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        default=100.00,
        help_text="Porcentaje de pagos realizados sin mora"
    )
    racha_actual_sin_mora = models.IntegerField(default=0, help_text="Pagos consecutivos sin mora")
    racha_maxima_sin_mora = models.IntegerField(default=0)

    # Pagos parciales vs completos
    total_pagos_completos = models.IntegerField(default=0)
    total_pagos_con_faltante = models.IntegerField(default=0)
    total_pagos_con_excedente = models.IntegerField(default=0)
    total_excedente_acumulado = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Informacion temporal 
    primer_pago = models.DateField(null=True, blank=True)
    ultimo_pago = models.DateField(null=True, blank=True)
    meses_como_cliente = models.IntegerField(default=0)
    
    # Metadata
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de Pago"
        verbose_name_plural = "Perfiles de Pago"
        
    
    def __str__(self):
        return f"Perfil de pago - {self.negocio.nombre}"
    
    def obtener_resumen(self):
        """
        Retorna un diccionario con el resumen de metricas para mostrar
        """

        return {
            'total_pagos': self.total_pagos_realizados,
            'total_pagado': f"Q.{self.total_monto_pagado:,.2f}",
            'promedio_pago': f"Q.{self.promedio_monto_pago:,.2f}",
            'dia_promedio': self.dia_promedio_pago,
            'metodo_preferido': self.metodo_preferido,
            'puntualidad': f"{self.porcentaje_puntualidad:.1f}%",
            'racha_sin_mora': self.racha_actual_sin_mora,
            'meses_cliente': self.meses_como_cliente,
            'total_mora': f"Q.{self.total_mora_pagada:,.2f}",
        }