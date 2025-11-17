from historiales.models import HistorialNegocio


def registrar_historial_negocio(negocio, accion, tipoCambio, descripcion, estadoAnterior=None, estadoNuevo=None):
    """
    Función centralizada para registrar cambios en el historial de un local.
    
    Args:
        local: Instancia del modelo Local
        accion: 'CREACION', 'ACTUALIZACION', 'ELIMINACION', 'CAMBIO'
        tipo_cambio: Descripción breve del tipo de cambio (ej: "nombre", "estado", "costo")
        descripcion: Descripción detallada del cambio
        estado_anterior: Valor anterior del campo (opcional)
        estado_nuevo: Valor nuevo del campo (opcional)
    """
    HistorialNegocio.objects.create(
        local=negocio,
        accion=accion,
        tipoCambio=tipoCambio,
        descripcion=descripcion,
        estadoAnterior=str(estadoAnterior) if estadoAnterior else None,
        estadoNuevo=str(estadoNuevo) if estadoNuevo else None
    )

def detectar_cambios_negocio(negocio_original, negocio_nuevo):
    """
    Detecta y registra los cambios específicos entre dos estados de un negocio.
    
    Args:
        negocio_original: Instancia del Local antes de los cambios
        negocio_nuevo: Instancia del Local después de los cambios
    
    Returns:
        Lista de descripciones de cambios realizados
    """
    cambios = []

    # Comparar cada campo relevante
    campos_a_comparar = {
        'nombre': 'Nombre',
        'costo': 'Costo',
        'estado': 'Estado',
        'nivel': 'Nivel',
        'ubicacion': 'Ubicacion',
        'posicionMapa': 'Posicion en el Mapa'
    }

    for campo, nombre_display in campos_a_comparar.items():
        valor_anterior = getattr(negocio_original, campo, None)
        valor_nuevo = getattr(negocio_nuevo, campo, None)

        # Convertir a string para convertir a comparacion consistente
        str_anterior = str(valor_anterior) if valor_anterior is not None else None
        str_nuevo = str(valor_nuevo) if valor_nuevo is not None else None

        if str_anterior != str_nuevo:
            descripcion = f"Se cambio {nombre_display} de '{valor_anterior}' a '{valor_nuevo}'"
            cambios.append(descripcion)

            registrar_historial_negocio(
                negocio=negocio_nuevo,
                accion='ACTUALIZACION',
                tipoCambio=campo,
                descripcion=descripcion,
                estadoAnterior=str_anterior,
                estadoNuevo=str_nuevo
            )
    return cambios