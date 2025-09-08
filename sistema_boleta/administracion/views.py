from django.shortcuts import render, get_object_or_404, redirect
from boletas.views import BoletaSandbox
from boletas.models import Boleta, EstadoBoleta, TipoPago
from transacciones.models import Transaccion
from boletas.services.email_ingestor.email_ingestor import procesar_correos
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from configuracion.models import Banco
from locales.models import OcupacionLocal
from negocios.models import Negocio
from django.views.decorators.http import require_POST
from django.contrib import messages
import os
from django.urls import reverse
from django.conf import settings
import shutil
from decimal import Decimal, InvalidOperation
from boletas.utils.mora import evaluar_pago, procesar_pago_faltante, detectar_pago_complementario
from boletas.utils.mensajes_estados import generar_mensaje
from email.utils import parsedate_to_datetime
from datetime import datetime

def boletas_sandbox(request):
    boletas = BoletaSandbox.objects.all().order_by('-fecha_recepcion') 
    return render(request, 'administracion/administracion.html', {
        'boletas': boletas
    })


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
            
            # ✅ PASO 1: Verificar si hay transacciones con faltante PRIMERO
            transacciones_pendientes = Transaccion.objects.filter(
                negocio=negocio,
                estado='espera_complemento',  # Estado específico de faltante
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
            
            # ✅ CASO 1: HAY FALTANTE PREVIO - Esta es la prioridad
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
                })
                
            # ✅ CASO 2: NO HAY FALTANTE, pero evaluar si hay MORA por tiempo
            else:
                # Evaluar la situación actual (sin monto específico, solo para obtener contexto)
                evaluacion = evaluar_pago(
                    fecha_original=fecha_original,
                    forma_pago="efectivo",  # Usar efectivo para obtener el escenario más directo
                    costo_local=costo_total,
                    monto_boleta=Decimal("0.00"),  # Monto 0 para solo obtener el contexto
                    negocio=negocio
                )
                
                cuota_original = evaluacion['costo_total']
                cuota_con_ajustes = evaluacion['monto_final']
                
                print(f"🔍 Debug - Cuota original: {cuota_original}")
                print(f"🔍 Debug - Cuota con ajustes: {cuota_con_ajustes}")
                print(f"🔍 Debug - Tiene mora: {evaluacion['mora_aplicada']}")
                
                # Actualizar contexto base
                contexto_cuota['cuota_original'] = cuota_original
                
                if cuota_con_ajustes > cuota_original:
                    # Caso: Hay mora o recargo por tiempo
                    diferencia = cuota_con_ajustes - cuota_original
                    contexto_cuota.update({
                        'tiene_ajustes': True,
                        'tipo': 'mora',
                        'cuota_ajustada': cuota_con_ajustes,
                        'diferencia': diferencia,
                        'tiene_mora': evaluacion['mora_aplicada'],
                        'porcentaje_mora': evaluacion.get('mora_monto', Decimal("0.00")),
                        'periodo_objetivo': evaluacion['periodo_pagado'],
                        'mensaje_contexto': f"Este negocio tiene un recargo por mora aplicado.",
                        'comentarios_relevantes': [c for c in evaluacion['comentarios'] if 'mora' in c.lower() or 'plazo' in c.lower()]
                    })
    
    # Debug final
    if contexto_cuota:
        print(f"🔍 Debug Final - tiene_faltante_previo: {contexto_cuota.get('tiene_faltante_previo', False)}")
        print(f"🔍 Debug Final - tiene_ajustes: {contexto_cuota.get('tiene_ajustes', False)}")
    
    # Obtener otros datos necesarios para el template
    tipos_pago = TipoPago.objects.all()
    bancos = Banco.objects.all()
    
    context = {
        'boleta': sandbox,
        'negocio': negocio,
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



def procesar_boleta(request, boleta_id):
    sandbox = get_object_or_404(BoletaSandbox, id=boleta_id)
    negocio_id = sandbox.metadata.get('negocio_id')
    negocio = Negocio.objects.get(idNegocio=negocio_id)
    ocupaciones = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
    ocupacion = ocupaciones.first()

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
        monto = request.POST.get('monto', "").replace(",", ".")
        numero_boleta = request.POST.get('numeroBoleta')
        banco_id = int(request.POST.get('banco'))
        fecha_deposito = request.POST.get('fechaDeposito') # Viene del form
        tipo_pago_id = request.POST.get('tipoPago') # Viene del modal final

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
                fecha_deposito_obj = datetime.strptime(fecha_deposito, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({
                    "success": False,
                    "tipo": "error",
                    "mensaje": "Formato de fecha invalido, usar (AAAA-MM-DD)",
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
            'mensaje': 'ERROR: No se puede procesar la transaccion',
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
    }
    return render(request, "administracion/perfil_transaccion.html", context)
