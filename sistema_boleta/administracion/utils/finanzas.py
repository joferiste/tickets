from decimal import Decimal
from transacciones.models import Transaccion

def detectar_pago_complementario(negocio, monto_pago):
    """
    Determina si el pago recibido debe aplicarse como complemento a una transaccion existente.

    negocio: instancia de negocio
    monto_pago: Decimal del monto ingresado en la boleta

    Retorna:
        transaccion existente a completar, o None si no hay transacciones pendientes.
    """

    if not isinstance(monto_pago, Decimal):
        try:
            monto_pago = Decimal(str(monto_pago))
        except:
            monto_pago = Decimal("0.00")

    # Buscar transacciones pendientes de pago para este negocio
    transacciones_pendientes = Transaccion.objects.filter(
        negocio=negocio,
        faltante__gt=0, # Aun tiene monto pendiente
    ).order_by('fecha_ingreso_sistema') # La mas antigua primero

    if transacciones_pendientes.exists():
        # Aplicar al mas antiguo
        return transacciones_pendientes.first()
    
    # Si no hay pendientes, retornar None
    return None