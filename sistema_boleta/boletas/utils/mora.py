from datetime import datetime, timezone as dt_timezone, timedelta
from email.utils import parsedate_to_datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from transacciones.models import Transaccion
from locales.models import OcupacionLocal
import calendar
from configuracion.models import Configuracion
from datetime import datetime as dt
from boletas.models import BoletaSandbox
from django.shortcuts import get_object_or_404
from boletas.models import Boleta, EstadoBoleta
from django.utils import timezone

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
            Transaccion.objects.filter(negocio=negocio)
            .values_list('periodo_pagado', flat=True)
        )
        periodo_dt = dt.strptime(periodo_boleta, "%Y-%m")
        while periodo_dt.strftime("%Y-%m") in ya_pagados:
            periodo_dt += relativedelta(months=1)
        periodo_pagado = periodo_dt.strftime("%Y-%m")

        if periodo_pagado != periodo_boleta:
            comentarios.append(f"Periodo {periodo_boleta} ya cubierto. Se asigna al siguiente libre: {periodo_pagado}.")
        else:
            comentarios.append(f"Pago para periodo: {periodo_pagado}")
    else:
        comentarios.append(f"Pago sin negocio asociado. Usando periodo: {periodo_pagado}")

    # --- Fecha límite del periodo_pagado ---
    year, month = map(int, periodo_pagado.split('-'))
    ultimo_dia = calendar.monthrange(year, month)[1]
    dia_corte = min(dias_sin_recargo, ultimo_dia)
    fecha_limite = datetime(year, month, dia_corte, tzinfo=dt_timezone.utc)
    fecha_limite_confirmacion = (base_fecha + timedelta(days=dias_confirmacion)).date()
    fecha_lapso_tiempo = base_fecha + timedelta(days=dias_confirmacion)

    # --- Calcular monto_final ---
    monto_final = costo_total

    # ---- Evaluación según forma de pago ----
    if forma_pago.lower() == "efectivo":
        estado = "en_revision"
        if base_fecha > fecha_limite:
            monto_final = (monto_final + mora_monto).quantize(Decimal("0.01"))
            mora_aplicada = True
            comentarios.append(f"Pago en efectivo fuera del plazo (límite: {fecha_limite.date()}). Mora {mora_porcentaje}% aplicada")
        else:
            comentarios.append(f"Pago en efectivo dentro del plazo (antes del {fecha_limite.date()}).")
    else:
        estado = "espera_confirmacion"    
        if hoy > fecha_limite_confirmacion:
            comentarios.append(
                f"Pago 'No en efectivo' fuera de la ventana de confirmación (+{dias_confirmacion} días desde {base_fecha.date()})"
            )
        else:
            comentarios.append(
                f"Pago 'No en efectivo' dentro de la ventana de confirmación hasta {fecha_limite_confirmacion}"
            )
        
        if base_fecha > fecha_limite:
            monto_final = (monto_final + mora_monto).quantize(Decimal("0.01"))
            mora_aplicada = True
            comentarios.append(f"Además, fuera del plazo del periodo (límite: {fecha_limite.date()}). Mora {mora_porcentaje}% aplicada.")

    # --- Excedentes / Faltantes sobre el monto_final ---
    excedente = Decimal("0.00")
    faltante = Decimal("0.00")
    
    if not isinstance(monto_boleta, Decimal):
        try:
            monto_boleta = Decimal(str(monto_boleta))
        except Exception:
            monto_boleta = Decimal("0.00")

    if monto_boleta > monto_final:
        excedente = (monto_boleta - monto_final).quantize(Decimal("0.01"))
        comentarios.append(f"Pago con excedente de Q.{excedente:.2f}.")
        if forma_pago.lower() == "efectivo":
            estado = "exitosa"
        else:
            estado = 'espera_acreditacion'
    elif monto_boleta < monto_final:
        faltante = (monto_final - monto_boleta).quantize(Decimal("0.01"))
        comentarios.append(f"Pago con faltante de Q.{faltante:.2f}.")
        estado = "espera_complemento"
    else:
        comentarios.append("Monto exacto.")
        if forma_pago.lower() == "efectivo":
            estado = "exitosa"
        else:
            estado = "espera_confirmacion"

    # Resta del monto generado si tiene aumento o no, con la boleta ingresada
    diferencia_monto_deuda = monto_final - monto_boleta

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
    }


def detectar_pago_complementario(negocio, monto_boleta):
    """
    Detecta si existe una transacción con faltante que pueda ser completada por esta boleta.
    Retorna la transacción encontrada o None.
    """
    transaccion_faltante = Transaccion.objects.filter(
        negocio=negocio,
        faltante__gt=0,
        estado__in=['espera_complemento']
    ).order_by('fechaTransaccion').first()
    
    if transaccion_faltante and monto_boleta <= transaccion_faltante.faltante:
        return transaccion_faltante
    return None


def procesar_pago_faltante(boleta, transaccion_original):
    """
    Procesa una boleta complementaria actualizando la transacción original.
    """
    # 1. Marcar boleta como complementaria
    boleta.es_complemetaria = True
    boleta.save(update_fields=['es_complemetaria'])

    # 2. Obtener fecha original desde metadata de la transacción original
    boleta_original = transaccion_original.boleta
    fecha_original = boleta_original.metadata.get('fecha_original')
    
    # 3. Verificar si está dentro del plazo de complemento
    dentro_plazo = dentro_plazo_complemento(fecha_original)
    
    # 4. Calcular nuevo faltante y totales
    nuevo_faltante = transaccion_original.faltante - boleta.monto
    nuevo_monto_total = transaccion_original.monto + boleta.monto
    
    # 5. Determinar nuevo estado
    if nuevo_faltante <= 0:
        nuevo_estado = 'exitosa'
        nuevo_excedente = abs(nuevo_faltante) if nuevo_faltante < 0 else Decimal('0.00')
        nuevo_faltante = Decimal('0.00')
        
        # Actualizar estado de la boleta original también
        estado_procesada = EstadoBoleta.objects.get(nombre='Procesada')
        boleta_original.estado = estado_procesada
        boleta_original.save(update_fields=['estado'])
        
    else:
        nuevo_estado = transaccion_original.estado
        nuevo_excedente = Decimal('0.00')
    
    # 6. Construir comentarios actualizados
    comentarios_base = transaccion_original.comentario
    
    # Remover comentario de faltante anterior si existe
    if "Pago con faltante de Q." in comentarios_base:
        comentarios_base = comentarios_base.split("Pago con faltante de Q.")[0].rstrip(", .")
    
    if nuevo_faltante <= 0:
        if nuevo_excedente > 0:
            comentario_complemento = f"Pago completado con boleta complementaria. Excedente: Q.{nuevo_excedente:.2f}"
        else:
            comentario_complemento = "Pago completado con boleta complementaria."
    else:
        comentario_complemento = f"Pago parcial con boleta complementaria. Faltante restante: Q.{nuevo_faltante:.2f}"
    
    comentarios_finales = f"{comentarios_base}. {comentario_complemento}"
    
    # 7. Si llegó fuera del plazo, puede aplicar mora adicional
    if not dentro_plazo and nuevo_faltante > 0:
        config = Configuracion.objects.filter(activo=True).first()
        if config:
            mora_porcentaje = Decimal(config.mora_porcentaje or 0)
            mora_adicional = (nuevo_monto_total * (mora_porcentaje / Decimal("100"))).quantize(Decimal("0.01"))
            comentarios_finales += f" Mora adicional por complemento tardío: Q.{mora_adicional:.2f}"
    
    # 8. Actualizar la transacción original
    transaccion_original.monto = nuevo_monto_total
    transaccion_original.faltante = nuevo_faltante
    transaccion_original.excedente = nuevo_excedente
    transaccion_original.estado = nuevo_estado
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