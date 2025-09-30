from datetime import datetime, timezone as dt_timezone, timedelta
from email.utils import parsedate_to_datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from transacciones.models import Transaccion
from locales.models import OcupacionLocal
import calendar
from configuracion.models import Configuracion
from datetime import datetime as dt
from django.shortcuts import get_object_or_404
from boletas.models import EstadoBoleta
from django.utils import timezone
from django.db.models import Q

def evaluar_pago(fecha_original, forma_pago, costo_local, monto_boleta, negocio=None):
    fecha_original_conv = parsedate_to_datetime(fecha_original)

    config = Configuracion.objects.filter(activo=True).first()
    if not config:
        return {
            "monto_final": Decimal(costo_local),
            "estado": "error",
            "comentarios": ["Sin configuración activa"],
            "periodo_pagado": None,
            "mora_aplicada": False,
            "mora_monto": Decimal("0"),
            "excedente": Decimal("0"),
            "faltante": Decimal("0"),
            "fecha_limite": None,
            "fecha_limite_confirmacion": None,
            "costo_total": Decimal(costo_local),
            "dias_mora": 0,
            # Campos para excedentes
            "excedentes_aplicados": Decimal("0.00"),
            "detalle_excedentes": [],
            "monto_original_sin_excedentes": Decimal(costo_local)
        }

    dias_sin_recargo   = int(config.dias_sin_recargo or 10)     
    mora_porcentaje    = Decimal(config.mora_porcentaje or 0)
    dias_confirmacion  = int(getattr(config, "dias_confirmacion", 3))

    # Parsear fecha_original y asegurar tzinfo
    try:
        fecha_original_dt = parsedate_to_datetime(fecha_original)
        if fecha_original_dt.tzinfo is None:    
            fecha_original_dt = fecha_original_dt.replace(tzinfo=dt_timezone.utc)
    except Exception:
        fecha_original_dt = datetime.now(dt_timezone.utc)

    base_fecha = fecha_original_dt

    # --- Costo base: suma de todos los locales activos del negocio ---
    if negocio:
        ocupaciones = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
        costo_total = sum((ocup.local.nivel.costo for ocup in ocupaciones), Decimal("0"))
        if costo_total == 0 and costo_local:
            costo_total = Decimal(costo_local)
    else:
        costo_total = Decimal(costo_local)

    # --- Periodo al que "apunta" el correo ---
    periodo_boleta = base_fecha.strftime("%Y-%m")
    periodo_pagado = periodo_boleta
    comentarios = []
    estado = "pendiente"
    mora_monto = (costo_total * (mora_porcentaje / Decimal("100"))).quantize(Decimal("0.01"))
    mora_aplicada = False
    
    #   Inicializar dias_mora para ambos casos
    hoy = datetime.now(dt_timezone.utc).date()
    dias_mora = (hoy - base_fecha.date()).days

    # --- Si el mes YA está pagado, asignar al primer mes libre hacia adelante ---
    if negocio:
        ya_pagados = set(
            Transaccion.objects.filter(
                negocio=negocio,
                estado__in=['exitosa', 'espera_acreditacion', 'espera_confirmacion', 'espera_confirmacion_faltante']
            ).values_list('periodo_pagado', flat=True)
        )

        # Si el periodo ya esta cubierto, buscar el siguiente libre
        periodo_dt = dt.strptime(periodo_boleta, "%Y-%m")
        while periodo_dt.strftime("%Y-%m") in ya_pagados:
            periodo_dt += relativedelta(months=1)
        periodo_pagado = periodo_dt.strftime("%Y-%m")

        if periodo_pagado != periodo_boleta:
            comentarios.append(f"Periodo {periodo_boleta} ya cubierto. Se asigna al siguiente libre: {periodo_pagado}.")
        else:
            comentarios.append(f"Pago para periodo: {periodo_pagado}")
    else:
        periodo_pagado = periodo_boleta
        comentarios.append(f"Pago sin negocio asociado. Usando periodo: {periodo_pagado}")

    # --- Fecha límite del periodo_pagado ---
    year, month = map(int, periodo_pagado.split('-'))
    ultimo_dia = calendar.monthrange(year, month)[1]
    dia_corte = min(dias_sin_recargo, ultimo_dia)
    fecha_limite = datetime(year, month, dia_corte, tzinfo=dt_timezone.utc)

    # Para determinar mora, usar la fecha actual vs el limite del periodo objetivo
    hoy = datetime.now(dt_timezone.utc)
    fecha_limite_confirmacion = (base_fecha + timedelta(days=dias_confirmacion)).date()
    fecha_lapso_tiempo = base_fecha + timedelta(days=dias_confirmacion)

    # --- Calcular monto_final ---
    monto_final = costo_total

    # ---- Evaluación según forma de pago ----
    if forma_pago.lower() == "efectivo":
        estado = "en_revision"
        # Para efectivo, comparar con fecha_original vs limite de periodo objetivo
        if base_fecha > fecha_limite:
            monto_final = (monto_final + mora_monto).quantize(Decimal("0.01"))
            mora_aplicada = True
            comentarios.append(f"Pago en efectivo fuera del plazo (límite: {fecha_limite.date()}). Mora {mora_porcentaje}% aplicada")
        else:
            comentarios.append(f"Pago en efectivo dentro del plazo (antes del {fecha_limite.date()}).")
    else:
        estado = "espera_confirmacion"    
        if hoy.date() > fecha_limite_confirmacion:
            comentarios.append(
                f"Pago 'No en efectivo' fuera de la ventana de confirmación (+{dias_confirmacion} días desde {base_fecha.date()})"
            )
        else:
            comentarios.append(
                f"Pago 'No en efectivo' dentro de la ventana de confirmación hasta {fecha_limite_confirmacion}"
            )
        
        # Para determinar mora en periodo_objetivo, usar fecha actual vs limite del periodo
        if hoy > fecha_limite:
            monto_final = (monto_final + mora_monto).quantize(Decimal("0.01"))
            mora_aplicada = True
            comentarios.append(f"Además, fuera del plazo del periodo (límite: {fecha_limite.date()}). Mora {mora_porcentaje}% aplicada.")


    # Logica nueva para aplicar excedentes faltantes
    monto_original_sin_excedentes = monto_final # Guarda el monto original para referencia
    excedentes_resultado = aplicar_excedentes_disponibles(negocio, monto_final)

    monto_final_ajustado = excedentes_resultado['monto_restante']
    excedentes_aplicados = excedentes_resultado['monto_aplicado']
    detalle_excedentes = excedentes_resultado['detalle']

    # Agregar comentarios sobre excedentes aplicados 
    if excedentes_aplicados > 0:
        comentarios.append(f"Se aplicaron Q.{excedentes_aplicados:.2f} de excedentes previos.")
        for detalle in detalle_excedentes:
            comentarios.append(
                f"• Q.{detalle['monto_aplicado']:.2f} del período {detalle['periodo_origen']} "
                f"(Trans. #{detalle['transaccion_id']})"
            )

    # Calculo final de excedentes aplicados
    # --- Excedentes / Faltantes sobre el monto_final ---
    excedente = Decimal("0.00")
    faltante = Decimal("0.00")
    
    if not isinstance(monto_boleta, Decimal):
        try: 
            monto_boleta = Decimal(str(monto_boleta))
        except Exception:
            monto_boleta = Decimal("0.00")
 
    if monto_boleta > monto_final_ajustado:
    # Existe excedente en esta transaccion
        excedente = (monto_boleta - monto_final_ajustado).quantize(Decimal("0.01"))

        if mora_aplicada:
            comentarios.append(f"Pago con mora {mora_porcentaje}% aplicada. Sobrepago de Q.{excedente:.2f}.")
        else:
            comentarios.append(f"Pago con excedente de Q.{excedente:.2f}")

        # Determina el estado según la forma de pago
        if forma_pago.lower() == "efectivo":
            estado = "espera_acreditacion"
        else:
            estado = "espera_confirmacion"

    elif monto_boleta < monto_final_ajustado:
        # Aun hay faltante despues de aplicar excedente
        faltante = (monto_final_ajustado - monto_boleta).quantize(Decimal("0.01"))
        comentarios.append(f"Pago con faltante de Q.{faltante:.2f}.")

        if forma_pago.lower() == "efectivo":
            estado = 'espera_complemento'
        else:
            estado = 'espera_confirmacion_faltante'
    else:
        # Monto exacto despues de aplicar excedentes
        if excedentes_aplicados > 0:
            comentarios.append("Monto exacto tras aplicar excedentes previos.")
        else:
            comentarios.append("Monto exacto.")

        # Determinar estado segun forma de pago
        if forma_pago.lower()  == "efectivo":
            estado = "exitosa" # Pago normal exacto con efectivo
        else:
            estado = 'espera_confirmacion' # En espera de confirmación de fondos
            

    # Resta del monto generado si tiene aumento o no, con la boleta ingresada
    diferencia_monto_deuda = monto_original_sin_excedentes - monto_boleta

    # DEBUG - Remover después
    print(f"=== DEBUG EXCEDENTE ===")
    print(f"monto_boleta: {monto_boleta}")
    print(f"monto_final_ajustado: {monto_final_ajustado}")
    print(f"excedente calculado: {excedente}")
    print(f"excedentes_aplicados: {excedentes_aplicados}")
    print(f"resultado que se retorna: {excedente}")
    print("========================")

    return {
        "fecha_original_conv": fecha_original_conv,
        "monto_boleta": monto_boleta,
        "monto_final": monto_final,                         
        "estado": estado,  
        "forma_pago": forma_pago,                                 
        "comentarios": comentarios,                         
        "periodo_pagado": periodo_pagado,                   
        "mora_aplicada": mora_aplicada,
        "dias_mora": dias_mora,
        "mora_monto": mora_monto if mora_aplicada else Decimal("0.00"),
        "excedente": excedente,
        "faltante": faltante,
        "fecha_limite": fecha_limite.date(),
        "fecha_limite_confirmacion": fecha_limite_confirmacion,
        "fecha_lapso_tiempo": fecha_lapso_tiempo,
        "diferencia_monto_deuda": diferencia_monto_deuda,
        "costo_total": costo_total,
        "mora_porcentaje": mora_porcentaje,
        # Nuevos campos para excedentes
        "excedentes_aplicados": excedentes_aplicados,
        "detalle_excedentes": detalle_excedentes,
        "monto_original_sin_excedentes": monto_original_sin_excedentes,
        "transacciones_excedentes_actualizadas": excedentes_resultado['transacciones_actualizadas'],
    }


def detectar_pago_complementario(negocio, monto_boleta):
    """
    Detecta si existe una transacción con faltante que pueda ser completada por esta boleta.
    Retorna la transacción encontrada o None.
    """
    transaccion_faltante = Transaccion.objects.filter(
        negocio=negocio,
        faltante__gt=0,
        estado__in=['espera_complemento', 'espera_complemento_faltante']
    ).order_by('-fechaTransaccion').first()
    
    if transaccion_faltante and monto_boleta <= transaccion_faltante.faltante:
        return transaccion_faltante
    return None


def procesar_pago_faltante(boleta, transaccion_original):
    """
    Procesa una boleta complementaria actualizando la transacción original.
    Usara la logica de evaluar_pago para manejar excedentes correcta
    """

    config = Configuracion.objects.filter(activo=True).first()
    mora_porcentaje = Decimal(config.mora_porcentaje or 0)
    # 1. Marcar boleta como complementaria
    boleta.es_complemetaria = True
    boleta.save(update_fields=['es_complemetaria'])

    # 2. Obtener datos necesarios para evaluar_pago
    boleta_original = transaccion_original.boleta
    fecha_original = boleta_original.metadata.get('fecha_original')
    forma_pago = boleta.tipoPago.nombre
    negocio = boleta.negocio
    
    # Obtener costo del local
    ocupaciones = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
    ocupacion = ocupaciones.first()
    costo_local = ocupacion.local.nivel.costo if ocupacion else Decimal("0.00")
    
    # 3. Calcular el nuevo monto total (original + complementario)
    nuevo_monto_total = transaccion_original.monto + boleta.monto

    # 4. USAR evaluar_pago para manejar excedentes correctamente
    resultado_pago = evaluar_pago(
        fecha_original=fecha_original,
        forma_pago=forma_pago,
        costo_local=costo_local,
        monto_boleta=nuevo_monto_total,  # El monto de la boleta complementaria
        negocio=negocio
    )
    
    # 5. Actualizar la transacción original con los resultados de evaluar_pago
    transaccion_original.monto = nuevo_monto_total
    transaccion_original.faltante = resultado_pago["faltante"]
    transaccion_original.excedente = resultado_pago["excedente"]
    transaccion_original.estado = resultado_pago["estado"]
    
    # 6. Construir comentarios actualizados
    comentarios_base = transaccion_original.comentario
    
    # Remover comentario de faltante anterior si existe
    if "Pago con faltante de Q." in comentarios_base:
        comentarios_base = comentarios_base.split("Pago con faltante de Q.")[0].rstrip(", .")
    
    # Agregar información del complemento
    if resultado_pago["faltante"] <= 0:
        if resultado_pago["excedente"] > 0:
            comentario_complemento = f"Pago completado con boleta complementaria. \nCubierta la mora generada del {mora_porcentaje}%  la cantidad de: Q.{resultado_pago['excedente']:.2f}"
        else:
            comentario_complemento = "Pago completado con boleta complementaria."
            
        # Actualizar estado de la boleta original también
        estado_procesada = EstadoBoleta.objects.get(nombre='Procesada')
        boleta_original.estado = estado_procesada
        boleta_original.save(update_fields=['estado'])
    else:
        comentario_complemento = f"Pago parcial con boleta complementaria. Faltante restante: Q.{resultado_pago['faltante']:.2f}"
    
    # Agregar información sobre excedentes aplicados
    if resultado_pago.get("excedentes_aplicados", Decimal("0.00")) > 0:
        comentario_complemento += f" Se aplicaron Q.{resultado_pago['excedentes_aplicados']:.2f} de excedentes previos."
    
    comentarios_finales = f"{comentarios_base}. {comentario_complemento}"
    
    # Agregar comentarios adicionales de evaluar_pago
    comentarios_evaluar = resultado_pago.get("comentarios", [])
    for comentario in comentarios_evaluar:
        if "excedente" in comentario.lower() or "faltante" in comentario.lower():
            comentarios_finales += f" {comentario}"
    
    transaccion_original.comentario = comentarios_finales
    transaccion_original.ultima_actualizacion = timezone.now()
    transaccion_original.save()
    return True  # Indica que se procesó como complementaria


def dentro_plazo_complemento(fecha_original):
    """
    Retorna True si la boleta complementaria llega antes del plazo límite
    """
    # Convertir fecha_original a datetime con timezone
    if isinstance(fecha_original, str):
        conv_fecha = parsedate_to_datetime(fecha_original)
    elif isinstance(fecha_original, datetime):
        conv_fecha = fecha_original
    else:
        # Si viene como date, lo convertimos a datetime a medianoche
        conv_fecha = datetime.combine(fecha_original, datetime.min.time())

    # Asegurar que tenga tz
    if conv_fecha is None or conv_fecha.tzinfo.utcoffset(conv_fecha) is None:
        conv_fecha = conv_fecha.replace(tzinfo=dt_timezone.utc)

    # Obtener configuración para días de confirmación
    config = Configuracion.objects.filter(activo=True).first()
    dias_confirmacion = int(getattr(config, "dias_confirmacion", 3)) if config else 3
    
    plazo_maximo = conv_fecha + timedelta(days=dias_confirmacion)

    # Normalizar ambos para comparar
    ahora = timezone.now().astimezone(dt_timezone.utc)
    plazo_maximo = plazo_maximo.astimezone(dt_timezone.utc)
    
    # ✅ Ambos datetimes ahora tienen timezone
    return ahora <= plazo_maximo


def buscar_excedentes_disponibles(negocio):
    """
    Busca todos los excedentes disponibles de un negocio en orden FIFO

    Returns:
        QuerySet de transacciones con excedente > 0, ordenadas por fecha
    """

    if not negocio:
        return Transaccion.objects.none()
    
    # DEBUG: Ver todas las transacciones del negocio
    todas = Transaccion.objects.filter(negocio=negocio)
    print(f"=== DEBUG BUSCAR EXCEDENTES ===")
    print(f"Total transacciones del negocio: {todas.count()}")
    
    for t in todas:
        print(f"  - Trans {t.idTransaccion}: excedente={t.excedente}, estado={t.estado}")
    
    resultado = Transaccion.objects.filter(
        negocio=negocio,
        excedente__gt=Decimal("0.00"),
        estado__in=["exitosa", "espera_acreditacion"] # Solo de transacciones exitosas
    ).order_by("fechaTransaccion") # FIFO - first in first out

    print(f"Transacciones con excedente filtradas: {resultado.count()}")
    print("==============================")

    return resultado


def aplicar_excedentes_disponibles(negocio, monto_requerido):
    """
    Aplica excedentes diponibles a un monto requerido en orden FIFO

    Args:
        negocio: instancia del negocio
        monto_requerido: Decimal - monto que se necesita cubrir

    Returns:
        dict con:
            - monto_aplicado: Decimal - total aplicado de excedentes
            - monto_restante: Decimal - lo que queda por pagar despues de aplicar excedente
            - detalle:  list - detalle de cada excedente aplicado
            - transacciones_actualizadas: list - IDs de transacciones modificadas
    """

    if not negocio or monto_requerido <= 0:
        return {
            'monto_aplicado': Decimal("0.00"),
            'monto_restante': monto_requerido,
            'detalle': [],
            'transacciones_actualizadas': []
        }
    
    excedentes_disponibles = buscar_excedentes_disponibles(negocio)
    monto_aplicado = Decimal("0.00")
    monto_restante = monto_requerido
    detalle = []
    transacciones_actualizadas = []

    # DEBUG
    print(f"=== DEBUG APLICAR EXCEDENTES ===")
    print(f"Negocio: {negocio}")
    print(f"Monto requerido: {monto_requerido}")
    print(f"Excedentes encontrados: {excedentes_disponibles.count()}")
    
    for t in excedentes_disponibles:
        print(f"  - Trans {t.idTransaccion}: excedente={t.excedente}, estado={t.estado}")
    print("==============================")

    for transaccion in excedentes_disponibles:
        if monto_restante <= 0:
            break # Ya se cubrio todo el monto requerido

        excedente_disponible = transaccion.excedente

        # Calcular cuanto de este excedente se puede usar
        monto_a_aplicar = min(excedente_disponible, monto_restante)

        # Actualizar la transaccion siempre que se use su excedente
        transaccion.excedente -= monto_a_aplicar

        # Si el excedente se agoto completamente, cambiar estado a exitosa
        if transaccion.excedente <= 0:
            transaccion.excedente = Decimal("0.00")
            transaccion.estado = "exitosa"

        # Guardar los cambios
        transaccion.save(update_fields=['excedente', 'estado', 'ultima_actualizacion'])

        # Actualizar contadores
        monto_aplicado += monto_a_aplicar
        monto_restante -= monto_a_aplicar

        # Registrar detalle para el mensaje
        detalle.append({
            'transaccion_id': transaccion.idTransaccion,
            'periodo_origen': transaccion.periodo_pagado,
            'excedente_original': excedente_disponible,
            'monto_aplicado': monto_a_aplicar,
            'excedente_restante': transaccion.excedente
        })

        transacciones_actualizadas.append(transaccion.idTransaccion)

    return {
            'monto_aplicado': monto_aplicado,
            'monto_restante': monto_restante,
            'detalle': detalle,
            'transacciones_actualizadas': transacciones_actualizadas
    }
