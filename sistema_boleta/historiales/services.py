from .models import HistorialTransaccion, HistorialNegocio, HistorialLocal
from .metrics import actualizar_metricas_negocio

def registrar_historial_transaccion(transaccion, accion, tipo_cambio,
                                    estado_anterior=None, estado_nuevo=None,
                                    descripcion='', observaciones=None):
    
    """
    Servicios para gestion de historiales
    Registra un evento en el historial del transacciones
    """

    # Determinar metodo de pago
    metodo_pago = 'Desconocido'
    if hasattr(transaccion, 'boleta') and transaccion.boleta:
        metodo_pago = transaccion.boleta.tipoPago.capitalize()

    # Determinar si tuvo mora
    tuvo_mora = transaccion.mora_monto > 0

    historial = HistorialTransaccion.objects.create(
        transaccion=transaccion,
        accion=accion,
        tipoCambio=tipo_cambio,
        estadoAnterior=estado_anterior,
        estadoNuevo=estado_nuevo,
        descripcion=descripcion,
        monto=transaccion.monto,
        metodo_pago=metodo_pago,
        periodo_pagado=transaccion.periodo_pagado,
        tuvo_mora=tuvo_mora,
        monto_mora=transaccion.mora_monto,
        dias_retraso=transaccion.dias_retraso,
        observaciones=observaciones
    )

    # Actualizar metricas si es exitosa
    if estado_nuevo == "exitosa":
        actualizar_metricas_negocio(transaccion.negocio)

    return historial


    # Funciones especificas de uso comun
def registrar_transaccion_creada(transaccion):
    """Atajo para registrar creacion"""
    return registrar_historial_transaccion(
        transaccion=transaccion,
        accion='CREACION',
        tipo_cambio='creacion_transaccion',
        estado_nuevo=transaccion.estado,
        descripcion=f"Transaccion creada para el para el período: {transaccion.periodo_pagado}"
    )

def registrar_validacion_boleta(transaccion):
    """Atajo para registrar validacion"""
    return registrar_historial_transaccion(
        transaccion=transaccion,
        accion='ACTUALIZACION',
        tipo_cambio='validacion_boleta',
        estado_anterior='espera_confirmacion',
        estado_nuevo='exitosa',
        descripcion=f"Boleta validada y transaccion confirmada. Monto: Q.{transaccion.monto:,.2f}"
    )

def registrar_aplicacion_mora(transaccion, mora_aplicada):
    """Registra la aplicación de mora a una transacción"""
    return registrar_historial_transaccion(
        transaccion=transaccion,
        accion='CAMBIO',
        tipo_cambio='aplicacion_mora',
        descripcion=f"Se aplicó mora de Q.{mora_aplicada:.2f} por {transaccion.dias_retraso} días de retraso"
    )


def registrar_pago_parcial(transaccion, faltante):
    """Registra un pago parcial"""
    return registrar_historial_transaccion(
        transaccion=transaccion,
        accion='ACTUALIZACION',
        tipo_cambio='pago_parcial',
        estado_nuevo='espera_complemento',
        descripcion=f"Pago parcial recibido. Faltante: Q.{faltante:.2f}",
        observaciones=f"Monto pagado: Q.{transaccion.monto:.2f}, Faltante: Q.{faltante:.2f}"
    )