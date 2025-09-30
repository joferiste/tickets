from django.shortcuts import render, get_object_or_404, redirect
from boletas.views import BoletaSandbox
from boletas.models import Boleta, EstadoBoleta, TipoPago
from transacciones.models import Transaccion
from boletas.services.email_ingestor.email_ingestor import procesar_correos
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from configuracion.models import Banco
from locales.models import OcupacionLocal
from negocios.models import Negocio
from django.views.decorators.http import require_POST
from django.contrib import messages
import os
import re 
import json
from django.urls import reverse
from django.conf import settings
import shutil
from decimal import Decimal, InvalidOperation
from boletas.utils.mora import evaluar_pago, procesar_pago_faltante, detectar_pago_complementario, buscar_excedentes_disponibles
from boletas.utils.mensajes_estados import generar_mensaje
from email.utils import parsedate_to_datetime
from datetime import datetime, date
from django.views.decorators.cache import cache_control
from configuracion.models import Configuracion
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from recibos.models import Recibo, EstadoRecibo
import unicodedata

def boletas_sandbox(request):
    boletas = BoletaSandbox.objects.all().order_by('-fecha_recepcion')   

    context = {
        'boletas': boletas,
        'total_boletas': boletas.count(),
        'unread_count': boletas.filter(leido=False).count(),
        'processed_count': boletas.filter(estado_validacion='procesada').count(),
        'pending_count': boletas.exclude(estado_validacion='procesada').count(),
    }

    return render(request, 'administracion/administracion.html', context)


def revisar_correos(request):
    if request.method == 'POST':
        try:
            cantidad = procesar_correos()
            if cantidad is None:
                cantidad = 0
            return JsonResponse({"mensaje": f"{cantidad} correos procesados."}, status=200)
        except Exception as e:
            print(f"[ERROR] Fallo al procesar correos: {e}")
            return JsonResponse({"mensaje": "Error interno al procesar el correo."}, status=500)
    return JsonResponse({'mensaje': 'Método no permitido'}, status=405)


def boleta_detalle(request, boleta_id):
    boleta = get_object_or_404(BoletaSandbox, id=boleta_id)

    boleta_sandbox = BoletaSandbox.objects.filter(id=boleta_id).first()

    negocio_id = boleta_sandbox.metadata.get("negocio_id")
    negocio = Negocio.objects.filter(idNegocio=negocio_id).first()
    print("[DEBUG] Negocio:", negocio)

    ocupacion = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True).first()
    print("[DEBUG] Ocupacion encontrada:", ocupacion)

    nombre_local = ocupacion.local.nombre

    # Marcar como leído si no lo está
    if not boleta.leido:
        boleta.leido = True
        boleta.save(update_fields=['leido'])
        
    return render(request, 'administracion/boleta_detalle.html', {'boleta':boleta, 'nombre_local':nombre_local})


def boletas_sandbox_parcial(request):
    boletas = BoletaSandbox.objects.all().order_by('-fecha_recepcion')
    html = render_to_string('administracion/_tabla_boletas.html', {'boletas':boletas})
    return JsonResponse({'html':html})


@require_POST
def eliminar_sandbox(request, boleta_id):
    boleta = get_object_or_404(BoletaSandbox, id=boleta_id)

    if boleta.estado_validacion == 'rechazada':
        boleta.delete()
        messages.success(request, "Boleta eliminada exitosamente")
        # Redirigir a una vista general 
        return redirect('administracion:boletas_sandbox')
    else:
        messages.error(request, "Sólo se pueden eliminar boletas rechazadas")
    return redirect('administracion:boleta_detalle', boleta_id=boleta.id)  # O adonde quieras redirigir

def formatear_periodo(periodo_str):
    """ Convierte 2025-09 a Septiembre de 2025 """
    meses = {
        '01': 'Enero', '02': 'Febrero', '03': 'Marzo', '04': 'Abril',
        '05': 'Mayo', '06': 'Junio', '07': 'Julio', '08': 'Agosto',
        '09': 'Septiembre', '10': 'Octubre', '11': 'Noviembre', '12': 'Diciembre'
    }

    ano, mes = periodo_str.split('-')

    return f"{meses[mes]} de {ano}"

def formatear_fecha(fecha_obj):
    """ Convierte date(2025, 9, 15) a '15 de septiembre de 2025' """
    meses = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }

    return f"{fecha_obj.day} de {meses[fecha_obj.month]} de {fecha_obj.year}"


def revisar_boletas(request, sandbox_id):
    sandbox = get_object_or_404(BoletaSandbox, id=sandbox_id)
    
    # Obtener datos básicos
    negocio_id = sandbox.metadata.get('negocio_id')
    negocio = Negocio.objects.get(idNegocio=negocio_id) if negocio_id else None
    usuario = negocio.usuario if negocio else None
    
    # CONTEXTO INFORMATIVO: Evaluar situación actual del negocio
    contexto_cuota = None
    
    if negocio:
        # Obtener ocupación activa
        ocupaciones = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
        ocupacion = ocupaciones.first()
        
        nombre_locales = ", ".join([ocup.local.nombre for ocup in ocupaciones])
        print("[DEBUG] locales encontrada:", nombre_locales)

        # Costo total base
        costo_total = sum([ocup.local.nivel.costo for ocup in ocupaciones])
        print("[DEBUG] Costo:", costo_total)

        if ocupacion:
            fecha_original = sandbox.metadata.get('fecha_original')
            costo_local = ocupacion.local.nivel.costo
            
            # PASO 1: Verificar si hay transacciones con faltante PRIMERO
            transacciones_pendientes = Transaccion.objects.filter(
                negocio=negocio,
                estado__in=['espera_confirmacion', 'espera_confirmacion_faltante', 'espera_complemento'],  # Estado específico de faltante
                faltante__gt=0  # Asegurar que tenga faltante > 0
            ).order_by('-fechaTransaccion')
            
            print(f"🔍 Debug - Negocio: {negocio.nombre}")
            print(f"🔍 Debug - Transacciones con faltante encontradas: {transacciones_pendientes.count()}")
            
            # Inicializar contexto_cuota
            contexto_cuota = {
                'cuota_original': Decimal(str(costo_total)),
                'tiene_ajustes': False,
                'tiene_faltante_previo': False,
            }

            excedentes_activos = Transaccion.objects.filter(
                negocio=negocio,
                excedente__gt=0,
                estado__in=['exitosa', 'espera_acreditacion']
            )

            if excedentes_activos.exists():
                contexto_cuota.update({
                    'tiene_excedentes_previos': True,
                    'excedentes_previos': excedentes_activos,
                    'mensaje_excedente': f"El negocio tiene Q.{sum(t.excedente for t in excedentes_activos):.2f} de excedentes disponibles."
                })
            
    config = Configuracion.objects.filter(activo=True).first()
    dias_sin_recargo = config.dias_sin_recargo if config else 5
    porcentaje_mora = config.mora_porcentaje if config else 5
    
    if fecha_original:
        try:
            fecha_boleta = datetime.strptime(fecha_original, "%Y-%m-%d").date()
        except:
            fecha_boleta = date.today()
    else:
        fecha_boleta = date.today()
            
    # CASO 1: HAY FALTANTE PREVIO - Esta es la prioridad
    if transacciones_pendientes.exists():
        transaccion_pendiente = transacciones_pendientes.first()
                
        print(f"🔍 Debug - Transacción pendiente: {transaccion_pendiente.idTransaccion}")
        print(f"🔍 Debug - Faltante: {transaccion_pendiente.faltante}")
        print(f"🔍 Debug - Estado: {transaccion_pendiente.estado}")
                
        contexto_cuota.update({
            'tiene_faltante_previo': True,
            'faltante_previo': transaccion_pendiente.faltante,
            'transaccion_pendiente': transaccion_pendiente,
            'periodo_pendiente': transaccion_pendiente.periodo_pagado,
            'mensaje_faltante': f"Existe un pago pendiente de completar para el período {transaccion_pendiente.periodo_pagado}.",
            # Información adicional útil
            'monto_ya_pagado': transaccion_pendiente.monto,
            'monto_total_requerido': transaccion_pendiente.monto + transaccion_pendiente.faltante,
            # AGREGAR CONTEXTO PARA ADMIN EN CASO DE FALTANTE
            'contexto_admin': {
                'tipo': 'faltante_previo',
                'titulo': f'Completar pago del período {formatear_periodo(transaccion_pendiente.periodo_pagado)}',
                'mensaje': f"Existe un pago pendiente que debe completarse antes de procesar nuevos pagos.",
                'detalles': [
                    f"Período: {formatear_periodo(transaccion_pendiente.periodo_pagado)}",
                    f"Monto ya pagado: Q.{transaccion_pendiente.monto:,.2f}",
                    f"Faltante por cubrir: Q.{transaccion_pendiente.faltante:,.2f}",
                    f"Monto total requerido: Q.{transaccion_pendiente.monto + transaccion_pendiente.faltante:,.2f}",
                ],
                'clase_css': 'contexto-faltante'
            }
        })

        print(f"\n Debug -- CONTEXTO FALTANTE PREVIO")
                
    # CASO 2: NO HAY FALTANTE, evaluar contexto completo del negocio
    else:
        # PASO 1: Determinar el período objetivo considerando excedentes
        periodo_objetivo = fecha_boleta.strftime("%Y-%m")
        
        # Verificar si el período actual ya está cubierto (incluyendo con excedentes)
        ya_pagados = set(
            Transaccion.objects.filter(
                negocio=negocio,
                estado__in=['exitosa', 'espera_acreditacion', 'espera_confirmacion', 'espera_confirmacion_faltante']
            ).values_list('periodo_pagado', flat=True)
        )
        
        # Si el período ya está cubierto, buscar el siguiente libre
        periodo_dt = datetime.strptime(periodo_objetivo, "%Y-%m").date()
        while periodo_dt.strftime("%Y-%m") in ya_pagados:
            periodo_dt = periodo_dt.replace(day=1) + relativedelta(months=1)
        periodo_objetivo = periodo_dt.strftime("%Y-%m")
        
        print(f"🔍 Debug - Período objetivo calculado: {periodo_objetivo}")
        print(f"🔍 Debug - Períodos ya pagados: {ya_pagados}")
        
        # PASO 2: Calcular si hay mora basado en el período objetivo (no la fecha de la boleta)
        año_objetivo, mes_objetivo = map(int, periodo_objetivo.split('-'))
        limite_periodo_objetivo = date(año_objetivo, mes_objetivo, dias_sin_recargo)
        
        # Usar la fecha actual para determinar si hay mora en el período objetivo
        hoy = date.today()
        tiene_mora_por_tiempo = hoy > limite_periodo_objetivo
        
        print(f"🔍 Debug - Límite período objetivo: {limite_periodo_objetivo}")
        print(f"🔍 Debug - Tiene mora por tiempo: {tiene_mora_por_tiempo}")

        # PASO 3: Obtener excedentes disponibles para aplicar
        excedentes_disponibles = buscar_excedentes_disponibles(negocio)
        total_excedentes_disponibles = sum(t.excedente for t in excedentes_disponibles) if excedentes_disponibles.exists() else Decimal('0')
        
        print(f"🔍 Debug - Total excedentes disponibles: {total_excedentes_disponibles}")
        print(f"🔍 Debug - Excedentes queryset: {list(excedentes_disponibles.values('idTransaccion', 'excedente', 'estado'))}")
        
        # PASO 4: Calcular cuota base para el período objetivo
        cuota_base = costo_total
        
        # Si hay mora, calcular cuota con mora
        if tiene_mora_por_tiempo:
            mora_decimal = Decimal(str(porcentaje_mora)) / Decimal('100')
            mora_monto = cuota_base * mora_decimal
            cuota_con_mora = cuota_base + mora_monto
        else:
            cuota_con_mora = cuota_base
            mora_monto = Decimal('0')
        
        # PASO 5: Aplicar excedentes disponibles
        monto_neto = cuota_con_mora - total_excedentes_disponibles
        monto_neto = max(monto_neto, Decimal('0'))  # No puede ser negativo
        
        # PASO 6: Determinar el contexto según la situación
        if total_excedentes_disponibles > 0:
            # HAY EXCEDENTES DISPONIBLES
            if monto_neto > 0:
                # Excedentes parciales - aún se debe algo
                contexto_cuota.update({
                    'cuota_original': cuota_base,
                    'tiene_ajustes': True,
                    'tipo': 'excedente_aplicado',
                    'cuota_con_mora': cuota_con_mora if tiene_mora_por_tiempo else None,
                    'mora_monto': mora_monto if tiene_mora_por_tiempo else None,
                    'excedentes_disponibles': total_excedentes_disponibles,
                    'monto_neto_a_pagar': monto_neto,
                    'cuota_ajustada': monto_neto,
                    'diferencia': total_excedentes_disponibles,
                    'periodo_objetivo': periodo_objetivo,
                    'mensaje_contexto': f"Se aplicarán Q.{total_excedentes_disponibles:.2f} de excedentes al período {periodo_objetivo}.",
                    'contexto_admin': {
                        'tipo': 'excedente_aplicado',
                        'titulo': f'Excedentes aplicados al período: {formatear_periodo(periodo_objetivo)}',
                        'mensaje': f"Se aplicarán excedentes disponibles para cubrir parte del pago.",
                        'detalles': [
                            f"Período: {formatear_periodo(periodo_objetivo)}",
                            f"Cuota base: Q.{cuota_base:,.2f}",
                            f"Mora aplicada: Q.{mora_monto:,.2f}" if tiene_mora_por_tiempo else "Sin mora",
                            f"Total requerido: Q.{cuota_con_mora:,.2f}",
                            f"Excedentes aplicados: Q.{total_excedentes_disponibles:,.2f}",
                            f"Monto neto a pagar: Q.{monto_neto:.2f}"
                        ],
                        'clase_css': 'contexto-excedente-aplicado'
                    }
                })
            else:
                # Excedentes cubren todo - pago completamente cubierto
                contexto_cuota.update({
                    'cuota_original': cuota_base,
                    'tiene_ajustes': True,
                    'tipo': 'cubierto_por_excedentes',
                    'cuota_con_mora': cuota_con_mora if tiene_mora_por_tiempo else None,
                    'excedentes_disponibles': total_excedentes_disponibles,
                    'excedente_restante': total_excedentes_disponibles - cuota_con_mora,
                    'monto_neto_a_pagar': Decimal('0'),
                    'cuota_ajustada': Decimal('0'),
                    'diferencia': cuota_con_mora,
                    'periodo_objetivo': formatear_periodo(periodo_objetivo),
                    'mensaje_contexto': f"El período {formatear_periodo(periodo_objetivo)} está completamente cubierto por excedentes.",
                    'contexto_admin': {
                        'tipo': 'cubierto_por_excedentes',
                        'titulo': f'Período {formatear_periodo(periodo_objetivo)} cubierto por excedentes',
                        'mensaje': f"Los excedentes disponibles cubren completamente el pago de este período.",
                        'detalles': [
                            f"Período objetivo: {formatear_periodo(periodo_objetivo)}",
                            f"Cuota base: Q.{cuota_base:,.2f}",
                            f"Mora aplicada: Q.{mora_monto:,.2f}" if tiene_mora_por_tiempo else "Sin mora",
                            f"Total requerido: Q.{cuota_con_mora:,.2f}",
                            f"Excedentes disponibles: Q.{total_excedentes_disponibles:,.2f}",
                            f"Excedente restante: Q.{total_excedentes_disponibles - cuota_con_mora:,.2f}",
                            "Monto a pagar: Q.0.00"
                        ],
                        'clase_css': 'contexto-cubierto'
                    }
                })
        else:
            # NO HAY EXCEDENTES - Lógica original pero actualizada
            if tiene_mora_por_tiempo:
                # MORA APLICADA
                contexto_cuota.update({
                    'cuota_original': cuota_base,
                    'tiene_ajustes': True,
                    'tipo': 'mora',
                    'cuota_ajustada': cuota_con_mora,
                    'diferencia': mora_monto,
                    'mora_monto': mora_monto,
                    'periodo_objetivo': periodo_objetivo,
                    'mensaje_contexto': f"Recargo por mora del {porcentaje_mora}% aplicado al período {formatear_periodo(periodo_objetivo)}.",
                    'contexto_admin': {
                        'tipo': 'mora',
                        'titulo': f'Recargo por Mora - Período {formatear_periodo(periodo_objetivo)}',
                        'mensaje': f"Se aplica recargo por mora al período: {formatear_periodo(periodo_objetivo)}.",
                        'detalles': [
                            f"Período: {formatear_periodo(periodo_objetivo)}",
                            f"Cuota base: Q.{cuota_base:,.2f}",
                            f"Recargo aplicado: {porcentaje_mora}%",
                            f"Monto de mora: Q.{mora_monto:,.2f}",
                            f"Total a pagar: Q.{cuota_con_mora:,.2f}",
                            f"Límite de pago: {formatear_fecha(limite_periodo_objetivo)}"
                        ],
                        'clase_css': 'contexto-mora'
                    }
                })
                print(f"\n🔍 Debug - CONTEXTO MORA APLICADO")
            else:
                # AL DÍA
                ultima_transaccion = Transaccion.objects.filter(
                    negocio=negocio,
                    estado='exitosa'
                ).order_by('-fechaTransaccion').first()
                
                contexto_cuota.update({
                    'cuota_original': cuota_base,
                    'tiene_ajustes': False,
                    'periodo_objetivo': periodo_objetivo,
                    'mensaje_contexto': f"Pago regular para el período {formatear_periodo(periodo_objetivo)}.",
                    'contexto_admin': {
                        'tipo': 'al_dia',
                        'titulo': f'Pago Regular - Período: {formatear_periodo(periodo_objetivo)}',
                        'mensaje': f"Pago regular sin ajustes para el período: {formatear_periodo(periodo_objetivo)}.",
                        'detalles': [
                            f"Período objetivo: {formatear_periodo(periodo_objetivo)}",
                            f"Cuota mensual: Q.{cuota_base:,.2f}",
                            f"Plazo de pago: hasta el día {dias_sin_recargo} de cada mes",
                            f"Última transacción: {ultima_transaccion.fechaTransaccion.strftime('%d-%m-%Y') if ultima_transaccion else 'Sin registros previos'}",
                            "Sin excedentes previos",
                            "Sin mora aplicada"
                        ],
                        'clase_css': 'contexto-al-dia'
                    }
                })
                print(f"\n🔍 Debug - CONTEXTO AL DÍA")
        
        print(f"🔍 Debug Final - Contexto determinado: {contexto_cuota.get('tipo', 'N/A')}")
        print(f"🔍 Debug Final - Período objetivo: {periodo_objetivo}")

    # Debug final
    print(f"🔍 Debug Final - Contexto tipo: {contexto_cuota.get('contexto_admin', {}).get('tipo', 'N/A')}")
    print(f"🔍 Debug Final - Tiene ajustes: {contexto_cuota.get('tiene_ajustes', False)}")
    
    # Obtener otros datos necesarios para el template
    tipos_pago = TipoPago.objects.all()
    bancos = Banco.objects.all()
    
    context = {
        'boleta': sandbox,
        'negocio': negocio,
        'hoy': date.today(),
        'tipos_pago': tipos_pago,
        'bancos': bancos,
        'ocupacion': ocupacion if 'ocupacion' in locals() else None,
        'usuario': usuario,
        'costo': costo_total,
        'nombre_local': nombre_locales,
        # CONTEXTO INFORMATIVO para el administrador
        'contexto_cuota': contexto_cuota,
    }
    return render(request, 'administracion/revision_boleta.html', context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def procesar_boleta(request, boleta_id):
    RE_BOLETA = re.compile(r'^\d{4,10}$')   # solo digitos 4 - 10 
    RE_MONTO = re.compile(r'^\d+([.,]\d{1,2})?$') # formato 1234, 1234.56. 1234,56

    sandbox = get_object_or_404(BoletaSandbox, id=boleta_id)
    negocio_id = sandbox.metadata.get('negocio_id')
    negocio = Negocio.objects.get(idNegocio=negocio_id)
    ocupaciones = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
    ocupacion = ocupaciones.first()
    fecha_str = request.POST.get('fechaDeposito')
    # Inicializar transaccion al inicio
    transaccion = None

    # ------- CASO 1: BOLETA YA PROCESADA -------
    if sandbox.estado_validacion == "procesada":
        return JsonResponse({
            "success": False,
            "tipo": "error",
            "mensaje": f"Esta boleta ya fue procesada el {sandbox.fecha_procesada.strftime('%d/%m/%Y %H:%M')}.",
            "transaccion_id": None
        })
    
    if request.method == 'POST':
        monto = (request.POST.get('monto') or '').strip()
        numero_boleta = (request.POST.get('numeroBoleta') or '').strip()
        banco_id = int(request.POST.get('banco'))
        fecha_str = request.POST.get('fechaDeposito') # Viene del form
        tipo_pago_id = request.POST.get('tipoPago') # Viene del modal final

        try:
            fecha_deposito = date.fromisoformat(fecha_str)
        except (TypeError, ValueError):
            return JsonResponse({
                'success': False,
                'tipo': 'error',
                'mensaje': 'Fecha Invalida',
                'transaccion_id': None,
            }, status=400)
        
        if fecha_deposito > date.today():
            return JsonResponse({
                'success': False,
                'tipo': 'error',
                'mensaje': 'No se admiten fechas mayores a la actual',
                'transaccion_id': None,
            }, status=400)

        # Validacion numero de boleta
        if not RE_BOLETA.fullmatch(numero_boleta):
            return JsonResponse({
                'success': False,
                'tipo': 'error',
                'mensaje': 'Número de boleta inválido, debe contener sólo dígitos',
                'transaccion_id': None,
            }, status=400)
        
        # Validacion monto
        if not RE_MONTO.fullmatch(monto):
            return JsonResponse({
                'success': False,
                'tipo': 'error',
                'mensaje': 'Monto no permitido, sujétese a los parámetros establecidos',
                'transaccion_id': None,
            }, status=400)
        
        normalized = monto.replace(',', '.')

        try:
            monto = Decimal(normalized)
        except (InvalidOperation, ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'tipo': 'error',
                'mensaje': 'Monto inválido, no se puede interpretar el número',
                'transaccion_id': None
            }, status=400)
        
        # Regla extra
        if monto <= 0:
            return JsonResponse({
                'success': False,
                'tipo': 'error',
                'mensaje': 'El monto debe de ser mayor a 0',
                'transaccion_id': None
            }, status=400)

        # --------- CASO 2: CAMPOS IMCOMPLETOS ---------
        if not numero_boleta or not banco_id or not tipo_pago_id:
            return JsonResponse({
                "success": False,
                "tipo": "error",
                "mensaje": "Faltan datos obligatorios: Número de boleta, banco o tipo de pago.",
                "transacciones_id": None
            })
        
        # Validar boleta duplicada  
        if Boleta.objects.filter(banco_id=banco_id, numeroBoleta=numero_boleta).exists():
            return JsonResponse({
                "success": False,
                "tipo": "error",
                "mensaje": f"La boleta {numero_boleta} ya está registrada para este banco.",
                "transacciones_id": None
            })
            
        # Parsear fecha_deposito
        fecha_deposito_obj = None
        if fecha_deposito:
            try:
                # Si fecha_deposito ya es objeto dato, usarlo directamente
                if isinstance(fecha_deposito, date):
                    fecha_deposito_obj = fecha_deposito
                # Si es string, convertirlo
                elif isinstance(fecha_deposito, str):
                    fecha_deposito_obj = datetime.strptime(fecha_deposito, "%Y-%m-%d").date()
                else:
                    # Si es otro tipo, intentar convertir a string primero
                    fecha_deposito_obj = datetime.strptime(str(fecha_deposito), "%Y-%m-%d").date()
            except (ValueError, TypeError):
                return JsonResponse({
                    "success": False,
                    "tipo": "error",
                    "mensaje": "Formato de fecha inválido, usar (AAAA-MM-DD)",
                    "transaccion_id": None
                })
            

        tipo_pago = TipoPago.objects.get(idTipoPago=tipo_pago_id)
        estado_procesada = EstadoBoleta.objects.get(nombre='Procesada')
        estado_en_revision = EstadoBoleta.objects.get(nombre='En Revisión')

        # Determinar estado según tipo de pago
        estado_boleta = estado_procesada

        TIPOS_PAGO_VALIDAR = {
                        'Cheque Propio', 
                        'Cheque Ajeno', 
                        'Cheque Exterior', 
                        'Por Definir'
                    }
        
        if tipo_pago.nombre in TIPOS_PAGO_VALIDAR:
            estado_boleta = estado_en_revision

        # Preparar monto como Decimal
        try:
            monto_limp = str(monto).replace(',','.').strip()
            monto_dec = Decimal(monto_limp)
        except (InvalidOperation, TypeError, ValueError):
            monto_dec = Decimal('0.00')

        
        transaccion_con_faltante = detectar_pago_complementario(negocio, monto_dec)

        if transaccion_con_faltante:
            # Es pago complementario - No crear nueva transaccion
                
            # Copiar imagen físicamente
            ruta_relativa = None
            if sandbox.imagen:
                origen = sandbox.imagen.path
                nueva_carpeta = os.path.join(settings.MEDIA_ROOT, 'boletas_procesadas')
                os.makedirs(nueva_carpeta, exist_ok=True)
                nombre_archivo = os.path.basename(origen)
                destino = os.path.join(nueva_carpeta, nombre_archivo)
                shutil.copy(origen, destino)
                ruta_relativa = os.path.join('boletas_procesadas', nombre_archivo)

            # Crear nombre para boleta complementaria
            fecha_formateada = timezone.now().strftime('%Y-%m-%d %H:%M')
            metadata = sandbox.metadata or {}
            nombre_negocio = metadata.get('negocio')

            if nombre_negocio:
                nombre_boleta = f"{nombre_negocio} - COMPLEMENTARIA - {fecha_formateada}"
            else:
                nombre_boleta = f"{sandbox.email} - COMPLEMENTARIA - {fecha_formateada}"

            # Crear boleta complementaria (SIN crear transacción nueva)
            nueva_boleta = Boleta.objects.create(
                nombre=nombre_boleta,
                email=sandbox.remitente,
                asunto=sandbox.asunto,
                metadata=sandbox.metadata,
                imagen=ruta_relativa,
                mensajeCorreo=sandbox.mensaje,
                monto=monto_dec,
                numeroBoleta=numero_boleta,
                banco_id=banco_id,
                origen='email',
                estado=estado_boleta,
                tipoPago=tipo_pago,
                negocio=negocio,
                es_complemetaria=True,  # Marcar como complementaria
                fechaDeposito=fecha_deposito_obj
            )

            # Procesar como complementaria (actualiza transacción existente)
            procesar_pago_faltante(nueva_boleta, transaccion_con_faltante)

            # Regenerar el mensaje después del procesamiento complementario 
            # Recargar la transaccion actualizada
            transaccion_con_faltante.refresh_from_db()

            # Preparar resultado_pago para generar_mensaje
            resultado_pago_actualizado = {
                "estado": transaccion_con_faltante.estado,
                "forma_pago": tipo_pago.nombre,
                "periodo_pagado": transaccion_con_faltante.periodo_pagado,
                "monto_boleta": transaccion_con_faltante.monto, # Ya incluye el complemento
                "faltante": transaccion_con_faltante.faltante,
                "excedente": transaccion_con_faltante.excedente,
                "mora_aplicada": transaccion_con_faltante.mora_monto > 0,
            }

            # Regenerar mensajes con la transaccion completa
            boleta_original = transaccion_con_faltante.boleta
            mensaje_actualizado = generar_mensaje(
                resultado_pago_actualizado, 
                boleta_nombre=boleta_original.nombre, # Usar nombre de boleta original
                complemento=True # Marcar como complemento para el mensaje correcto
            )

            # Actualizar el mensaje en la transaccion
            transaccion_con_faltante.mensaje_final = mensaje_actualizado
            transaccion_con_faltante.save(update_fields=['mensaje_final'])

            # Asignar la transaccion para uso posterior
            transaccion = transaccion_con_faltante
            
            messages.success(request, "Boleta complementaria procesada correctamente.")
            
        else:
            # ES PAGO NUEVO - crear transaccion normal
            # Obtener datos para evaluar_pago
            forma_pago = tipo_pago.nombre
            costo_local = ocupacion.local.nivel.costo
            fecha_original = sandbox.metadata.get('fecha_original')

            resultado_pago = evaluar_pago(fecha_original, forma_pago, costo_local, monto_dec, negocio=negocio)

            # Copiar imagen físicamente
            ruta_relativa = None
            if sandbox.imagen:
                origen = sandbox.imagen.path
                nueva_carpeta = os.path.join(settings.MEDIA_ROOT, 'boletas_procesadas')
                os.makedirs(nueva_carpeta, exist_ok=True)
                nombre_archivo = os.path.basename(origen)
                destino = os.path.join(nueva_carpeta, nombre_archivo)
                shutil.copy(origen, destino)
                ruta_relativa = os.path.join('boletas_procesadas', nombre_archivo)

            # Crear nombre para boleta nueva
            fecha_formateada = timezone.now().strftime('%Y-%m-%d %H:%M')
            metadata = sandbox.metadata or {}           
            nombre_negocio = metadata.get("negocio")

            if nombre_negocio:
                nombre_boleta = f"{nombre_negocio} - {fecha_formateada}"
            else:
                nombre_boleta = f"{sandbox.email} - {fecha_formateada}"

            # Crear nueva boleta
            nueva_boleta = Boleta.objects.create(
                nombre=nombre_boleta,
                email=sandbox.remitente,
                asunto=sandbox.asunto,
                metadata=sandbox.metadata, 
                imagen=ruta_relativa,
                mensajeCorreo=sandbox.mensaje,
                monto=monto_dec,
                numeroBoleta=numero_boleta,
                banco_id=banco_id,
                origen='email',
                estado=estado_boleta,
                tipoPago=tipo_pago,
                negocio=negocio,
                es_complemetaria=False,
                fechaDeposito=fecha_deposito_obj
            )
            print(f"Guardando transacción con excedente: {resultado_pago['excedente']}")
            # Crear transacción nueva
            transaccion = Transaccion.objects.create(
                boleta=nueva_boleta,
                negocio=nueva_boleta.negocio,
                monto=monto_dec,
                estado=resultado_pago["estado"],
                comentario=", ".join(resultado_pago["comentarios"]),
                periodo_pagado=resultado_pago["periodo_pagado"],
                mora_monto=resultado_pago["mora_monto"],
                faltante=resultado_pago["faltante"],
                excedente=resultado_pago["excedente"],
                dias_retraso=resultado_pago['dias_mora'],
                fecha_limite_confirmacion=resultado_pago['fecha_lapso_tiempo'],
                fecha_ingreso_sistema=resultado_pago['fecha_original_conv']
            )
            

            # Guardar mensaje humanizado en la transaccion para usarlo después
            transaccion.mensaje_final = generar_mensaje(resultado_pago, boleta_nombre=nueva_boleta.nombre, complemento=nueva_boleta.es_complemetaria)
            transaccion.save(update_fields=['mensaje_final'])


        # Marcar el sandbox como procesado
        sandbox.procesado = True
        sandbox.estado_validacion = 'procesada'
        sandbox.fecha_procesada = datetime.now()
        sandbox.save()

    if transaccion is None:
        return JsonResponse({
            'success': False,
            'tipo': 'error',
            'mensaje': 'ERROR: No se puede procesar la transacción',
            'transaccion_id': None
        }, status=500)

    tipo_modal = get_tipo_modal_resultado(transaccion.estado, transaccion.faltante)

    return JsonResponse({
        'success': True,
        'tipo': tipo_modal,
        'mensaje': transaccion.mensaje_final,
        'transaccion_id': transaccion.idTransaccion,
        'redirect_url': reverse('administracion:perfil_transaccion', kwargs={'transaccion_id':transaccion.idTransaccion})
    })

def get_tipo_modal_resultado(estado, faltante):
    # Determina que tipo de modal mostrar segun el resultado
    if estado == 'exitosa' and faltante == 0:
        return 'exitoso'
    elif estado in ['espera_complemento', 'espera_confirmacion', 'espera_acreditacion']:
        return 'pendiente'
    else:
        return 'error'



def perfil_transaccion(request, transaccion_id):
    transaccion = get_object_or_404(Transaccion, idTransaccion=transaccion_id)

    try:
        fecha = datetime.strptime(transaccion.periodo_pagado, "%Y-%m")
        periodo_legible = fecha.strftime("%B %Y")
    except ValueError:
        periodo_legible = transaccion.periodo_pagado

    # Boleta asociada
    boleta = transaccion.boleta

    # Negocio y locales
    negocio = boleta.negocio

    # Ocupaciones activas del negocio
    ocup_qs = (
        OcupacionLocal.objects
        .filter(negocio=negocio, fecha_fin__isnull=True)
        .select_related('local__nivel')
    )

    # Desduplicar por local_id (por si hubiera registros duplicados por error)
    visto = set()
    locales = []
    for oc in ocup_qs:
        if oc.local_id not in visto:
            visto.add(oc.local_id)
            locales.append(oc.local)

    # Calculo total base de los locales unicos
    costo_locales = sum(loc.nivel.costo for loc in locales)

    # Total a pagar (incluye mora si aplica)
    total_a_pagar = costo_locales + transaccion.mora_monto

    es_pago_efectivo_y_completo = (
        transaccion.boleta.tipoPago.nombre == "Efectivo"
        and transaccion.monto >= total_a_pagar
    )

    puede_generar_recibo = (
        transaccion.estado in ["exitosa", "espera_acreditacion"]
        and transaccion.faltante == 0
    )

    context = {
        "transaccion": transaccion,
        "boleta": boleta,
        "negocio": negocio,
        "locales": locales,
        "costo_locales": costo_locales,
        "total_a_pagar": total_a_pagar, 
        "ocultar_mora": es_pago_efectivo_y_completo,
        "periodo_legible": periodo_legible,
        "mensaje_final": transaccion.mensaje_final,
        "puede_generar_recibo": puede_generar_recibo,
    }
    return render(request, "administracion/perfil_transaccion.html", context)



@require_POST
def validar_transaccion(request, transaccion_id):
    """
    Vista para validar o rechazar una transaccion pendiente de confirmacion
    """
    print(f"Vista llamada con ID:  {transaccion_id}")
    print(f"Método: {request.method}")
    print(f"Body: {request.body}")
    try:
        # Obtener la transaccion
        transaccion_obj = get_object_or_404(Transaccion, idTransaccion=transaccion_id)

        # Verificar que la transaccion este en un estado correcto para validar
        estados_validos = ['espera_confirmacion', 'espera_confirmacion_faltante']
        if transaccion_obj.estado not in estados_validos:
            return JsonResponse({
                'status': 'error',
                'message': f'La transacción no está en estado válido para confirmación. Estado actual: {transaccion_obj.estado}'
            })
        
        # Parsear el body de la request
        data = json.loads(request.body)
        validado = data.get('validado', False)

        # Usar transaccion de base de datos para generar consistencia
        with transaction.atomic():
            if validado:
                # VALIDAR TRANSACCION
                if transaccion_obj.estado == 'espera_confirmacion_faltante':
                    #Validó el cheque, pero aun falta dinero -> sigue esperando complemento
                    transaccion_obj.estado = 'espera_complemento'
                    mensaje = 'Cheque validado, pendiente complemento de pago'

                    # Cambio interno: forzar cambio de TipoPago a efectivo
                    try:
                        tipo_efectivo = TipoPago.objects.get(nombre__iexact='Efectivo')
                        boleta_obj = transaccion_obj.boleta
                        boleta_obj.tipoPago = tipo_efectivo
                        boleta_obj.save(update_fields=['tipoPago'])
                    except TipoPago.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': "No existe el tipo de pago 'Efectivo'.",
                        })
                else:
                    # Validar transaccion normal
                    transaccion_obj.estado = 'exitosa'
                    #Actualizar timestamp
                    transaccion_obj.ultima_actualizacion = timezone.now()

                    # Si habia excedente, cambiar estado a espera_acreditacion
                    if transaccion_obj.excedente > 0:
                        transaccion_obj.estado = 'espera_acreditacion'

                    # Cambio interno: forzar cambio de TipoPago a efectivo
                    try:
                        tipo_efectivo = TipoPago.objects.get(nombre__iexact='Efectivo')
                        boleta_obj = transaccion_obj.boleta
                        boleta_obj.tipoPago = tipo_efectivo
                        boleta_obj.save(update_fields=['tipoPago'])
                    except TipoPago.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': "No existe el tipo de pago 'Efectivo'.",
                        })
                
                    # Cambiar interno: cambiar estado de boleta, de 'en revision' a 'procesada'
                    try:
                        estado_original = EstadoBoleta.objects.get(nombre__iexact='Procesada')
                        boleta_estado = transaccion_obj.boleta
                        boleta_estado.estado = estado_original
                        boleta_estado.save(update_fields=['estado'])
                    except EstadoBoleta.DoesNotExist:
                        return JsonResponse({
                            'status': 'error',
                            'message': "No existe el estado 'procesada'.",
                        })
                    
                    # Agregar comentario de validacion
                    comentario_validacion = f" Transacción validada el: {timezone.now().strftime('%d/%m/%Y a las %H:%M')}."
                    transaccion_obj.comentario += comentario_validacion
                    mensaje = 'Transacción validada correctamente'

            else:
                # Rechazar transaccion
                transaccion_obj.estado = 'rechazada'
                transaccion_obj.ultima_actualizacion = timezone.now()

                # Agregar comentario de rechazo
                comentario_rechazo = f" Transacción rechazada el: {timezone.now().strftime('%d-%m-%Y a las %H:%M')}."
                transaccion_obj.comentario += comentario_rechazo
                mensaje = 'Transacción rechazada.'

                # Si la transaccion tenia excedente, liberarlo (colocarlo disponible)
                if transaccion_obj.excedente > 0:
                    transaccion_obj.estado = 'espera_complemento'
                else:
                    transaccion_obj.estado = 'exitosa'

                
            
            # Generar resumen de pago actualizado
            resultado_pago = {
                "estado": transaccion_obj.estado,
                "forma_pago": "Efectivo" if validado else transaccion_obj.boleta.tipoPago.nombre,
                "periodo_pagado": transaccion_obj.periodo_pagado,
                "monto_boleta": transaccion_obj.monto,
                "faltante": transaccion_obj.faltante,
                "excedente": transaccion_obj.excedente,
            }

            nuevo_resumen = generar_mensaje(resultado_pago, boleta_nombre=transaccion_obj.boleta.nombre)
            transaccion_obj.mensaje_final = nuevo_resumen


            # Guardar cambios
            transaccion_obj.save()

        return JsonResponse({
            'status': 'success',
            'message': mensaje,
            'nuevo_estado': transaccion_obj.estado
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
        'status': 'error',
        'message': 'Error en el formato de los datos inválidos',
    })

    except Transaccion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Transacción no encontrada',
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error interno en el servidor: {str(e)}'
        })

def slugify_filename(nombre: str) -> str:
    # Normalizar (quta tildes)
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode(('ascii'))
    # Reemplazar caracteres no alfanumericos por _
    nombre = re.sub(r'\W+', '_', nombre)
    #Limitar longitud
    return nombre[:25]


def generar_recibo(request, transaccion_id):
    """
    Vista para generar el recibo oficial de una transacción exitosa
    """
    try:
        # Obtener la transacción
        transaccion_obj = get_object_or_404(Transaccion, idTransaccion=transaccion_id)
        
        estados_hacer_recibo = ['exitosa', 'espera_acreditacion']
        # Verificar que la transacción esté en estado exitoso o espera_acreditacion
        if transaccion_obj.estado not in estados_hacer_recibo:
            return JsonResponse({
                'status': 'error',
                'message': f'Sólo se pueden generar recibos para transacciones exitosas. Estado actual: {transaccion_obj.estado}'
            })
        
        recibo_existente = Recibo.objects.filter(transaccion=transaccion_obj).first()
        if recibo_existente:
            # Si ya existe, descargarlo
            response = HttpResponse(
                recibo_existente.archivo.read(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'inline; filename="{recibo_existente.nombre}"'
            return response
        
        # Generar nuevo recibo
        with transaction.atomic():
            # Generar correlativo unico
            ultimo_recibo = Recibo.objects.order_by('-correlativo').first()
            if ultimo_recibo and ultimo_recibo.correlativo.isdigit():
                nuevo_correlativo = str(int(ultimo_recibo.correlativo) + 1).zfill(6)
            else:
                nuevo_correlativo = "000001"

            #Generar nombre del recibo
            fecha_actual = timezone.now().strftime('%Y%m%d')
            negocio_limpio = slugify_filename(transaccion_obj.negocio.nombre)
            nombre_recibo = f"REC-{nuevo_correlativo}-{fecha_actual}-{negocio_limpio}"

            # Obtener estado inicial de recibo
            estado_generado, created = EstadoRecibo.objects.get_or_create(
                nombre='Generado',
                defaults={'nombre': 'Generado'}
            )

            # Crear el recibo (esto disparara el signal para generar el PDF)
            nuevo_recibo = Recibo.objects.create(
                correlativo=nuevo_correlativo,
                nombre=nombre_recibo,
                transaccion=transaccion_obj,
                email=transaccion_obj.boleta.email,
                estado=estado_generado
            )

            # Esperar a que signal genere el PDF
            nuevo_recibo.refresh_from_db()

            if nuevo_recibo.archivo and nuevo_recibo.archivo.name:
                try:
                    response = HttpResponse(
                        nuevo_recibo.archivo.read(),
                        content_type='application/pdf'
                    )
                    response['Content-Disposition'] = f'inline; filename="{nuevo_recibo.nombre}.pdf"'
                    return response
                except ValueError as e:
                    print(f"Error leyendo archivo: {e}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Error al leer el archivo PDF. Signal error: {str(e)}"
                    })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Error al generar el archivo PDF.'
                })
            
    except Transaccion.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Transacción no encontrada'
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al generar recibo: {str(e)}'
        })