from historiales.models import HistorialLocal, HistorialNegocio


def registrar_historial_local(local, accion, tipo_cambio, descripcion, estado_anterior=None, estado_nuevo=None):
    """
    Función centralizada para registrar cambios en el historial de un local.
    """
    HistorialLocal.objects.create(
        local=local,
        accion=accion,
        tipoCambio=tipo_cambio,
        descripcion=descripcion,
        estadoAnterior=str(estado_anterior) if estado_anterior else None,
        estadoNuevo=str(estado_nuevo) if estado_nuevo else None
    )


def registrar_historial_negocio(negocio, accion, tipo_cambio, descripcion, estado_anterior=None, estado_nuevo=None):
    """
    Función centralizada para registrar cambios en el historial de un negocio.
    """
    HistorialNegocio.objects.create(
        negocio=negocio,
        accion=accion,
        tipoCambio=tipo_cambio,
        descripcion=descripcion,
        estadoAnterior=str(estado_anterior) if estado_anterior else None,
        estadoNuevo=str(estado_nuevo) if estado_nuevo else None
    )




def registrar_asignacion_local(local, negocio, fecha_inicio):
    """
    Registra en el historial la asignación de un negocio a un local.
    Crea registros en ambos historiales (Local y Negocio).
    
    Args:
        local: Instancia del Local asignado
        negocio: Instancia del Negocio asignado
        fecha_inicio: Fecha de inicio de la ocupación
    """
    # Registrar en historial del LOCAL
    registrar_historial_local(
        local=local,
        accion='CAMBIO',
        tipo_cambio='asignacion_negocio',
        descripcion=f"Local asignado al negocio '{negocio.nombre}' desde {fecha_inicio.strftime('%d/%m/%Y')}.",
        estado_anterior='Disponible',
        estado_nuevo=f'Ocupado por {negocio.nombre}'
    )
    
    # Registrar en historial del NEGOCIO 
    registrar_historial_negocio(
        negocio=negocio,
        accion='CAMBIO',
        tipo_cambio='asignacion_local',
        descripcion=f"Negocio asignado al local '{local.nombre}' desde {fecha_inicio.strftime('%d/%m/%Y')}.",
        estado_anterior='Sin local asignado',
        estado_nuevo=f'Ocupa local {local.nombre}'
    )


def registrar_desasignacion_local(local, negocio, fecha_inicio, fecha_fin):
    """
    Registra en el historial la desasignación de un negocio de un local.
    Crea registros en ambos historiales (Local y Negocio).
    
    Args:
        local: Instancia del Local desasignado
        negocio: Instancia del Negocio desasignado
        fecha_inicio: Fecha de inicio de la ocupación
        fecha_fin: Fecha de fin de la ocupación
    """
    # Calcular duración de la ocupación
    duracion = (fecha_fin - fecha_inicio).days
    
    # Registrar en historial del LOCAL
    registrar_historial_local(
        local=local,
        accion='CAMBIO',
        tipo_cambio='desasignacion_negocio',
        descripcion=f"Local liberado del negocio '{negocio.nombre}' después de {duracion} días de ocupación.",
        estado_anterior=f'Ocupado por {negocio.nombre}',
        estado_nuevo='Disponible'
    )
    
    # Registrar en historial del NEGOCIO
    registrar_historial_negocio(
        negocio=negocio,
        accion='CAMBIO',
        tipo_cambio='desasignacion_local',
        descripcion=f"Negocio dejó el local '{local.nombre}' después de {duracion} días (desde {fecha_inicio.strftime('%d/%m/%Y')} hasta {fecha_fin.strftime('%d/%m/%Y')}).",
        estado_anterior=f'Ocupa local {local.nombre}',
        estado_nuevo='Sin local asignado'
    )




def detectar_cambios_local(local_original, local_nuevo):
    """
    Detecta y registra los cambios específicos entre dos estados de un local.
    """
    cambios = []
    
    campos_a_comparar = {
        'nombre': 'Nombre',
        'costo': 'Costo',
        'estado': 'Estado',
        'nivel': 'Nivel',
        'ubicacion': 'Ubicación',
        'posicionMapa': 'Posición en el mapa'
    }
    
    for campo, nombre_display in campos_a_comparar.items():
        valor_anterior = getattr(local_original, campo, None)
        valor_nuevo = getattr(local_nuevo, campo, None)
        
        str_anterior = str(valor_anterior) if valor_anterior is not None else None
        str_nuevo = str(valor_nuevo) if valor_nuevo is not None else None
        
        if str_anterior != str_nuevo:
            descripcion = f"Se cambió {nombre_display} de '{valor_anterior}' a '{valor_nuevo}'"
            cambios.append(descripcion)
            
            registrar_historial_local(
                local=local_nuevo,
                accion='ACTUALIZACION',
                tipo_cambio=campo,
                descripcion=descripcion,
                estado_anterior=str_anterior,
                estado_nuevo=str_nuevo
            )
    
    return cambios

def detectar_cambios_negocios(negocio_original, negocio_nuevo):
    """
    Detecta y registra los cambios específicos entre dos estados de un local.
    """
    cambios = []
    
    campos_a_comparar = {
        'nombre': 'Nombre',
        'descripcion': 'Descripción',
        'telefono1': 'Telefono 1',
        'telefono2': 'Telefono 2',
        'email': 'Correo Electronico',
        'nit': 'NIT',
        'estado': 'Estado',
        'categoria': 'Categoría'
    }
    
    for campo, nombre_display in campos_a_comparar.items():
        valor_anterior = getattr(negocio_original, campo, None)
        valor_nuevo = getattr(negocio_nuevo, campo, None)
        
        str_anterior = str(valor_anterior) if valor_anterior is not None else None
        str_nuevo = str(valor_nuevo) if valor_nuevo is not None else None
        
        if str_anterior != str_nuevo:
            descripcion = f"Se cambió {nombre_display} de '{valor_anterior}' a '{valor_nuevo}'"
            cambios.append(descripcion)
            
            registrar_historial_negocio(
                negocio=negocio_nuevo,
                accion='ACTUALIZACION',
                tipo_cambio=campo,
                descripcion=descripcion,
                estado_anterior=str_anterior,
                estado_nuevo=str_nuevo
            )
    
    return cambios