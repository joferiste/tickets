from decimal import Decimal
import calendar

def generar_mensaje(resultado_pago, boleta_nombre=None, complemento=False):
    """
    Genera un mensaje humanizado basado en la evolución de la boleta a lo largo de su vida dentro del sistema
    
    resultado_pago: dict devuelto por evaluar_pago o procesar_pago_faltante
    boleta_nombre: nombre de la boleta (opcional, util para mensajes complementarios)
    complemento: True si la boleta es complementaria
    """
    
    # Mapeo de estados a descripciones legibles
    ESTADOS_DESC = {
        'pendiente': 'Pendiente',
        'en_revision': 'En revisión',
        'espera_confirmacion': 'En espera de confirmación de fondos',
        'espera_confirmacion_faltante': 'En espera de confirmación - Con faltante', 
        'espera_complemento': 'Espera de complemento de pago',
        'espera_acreditacion': 'Espera de acreditación de saldo a favor',
        'procesada': 'Procesada',
        'exitosa': 'Exitosa',
        'rechazada': 'Rechazada',
        'fallida': 'Fallida'
    }
    
    # Mapeo de meses en español
    MESES_ES = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    estado = resultado_pago.get("estado", "desconocido")
    forma_pago = resultado_pago.get("forma_pago", "No especificada")
    periodo = resultado_pago.get("periodo_pagado", "desconocido")
    monto = resultado_pago.get("monto_boleta", Decimal("0.00"))
    faltante = resultado_pago.get("faltante", Decimal("0.00"))
    excedente = resultado_pago.get("excedente", Decimal("0.00"))
    mora_aplicada = resultado_pago.get("mora_aplicada", False)
    excedentes_aplicados = resultado_pago.get("excedentes_aplicados", Decimal("0.00"))
    detalle_excedentes = resultado_pago.get("detalle_excedentes", [])
    monto_original = resultado_pago.get("monto_original_sin_excedentes", Decimal("0.00"))

    # Convertir estado a descripción legible
    estado_desc = ESTADOS_DESC.get(estado, estado)

    # Si el periodo viene tipo 2025-08 mostrar "Agosto de 2025" 
    if isinstance(periodo, str) and "-" in periodo:
        try:
            ano, mes = periodo.split("-")
            mes_numero = int(mes)
            mes_nombre = MESES_ES.get(mes_numero, f"Mes {mes}")
            periodo = f"{mes_nombre} de {ano}"
        except Exception:
            pass

    mensaje = f"Resumen de pago para: {boleta_nombre or ''}.\n\n" if boleta_nombre else "Resumen de pago\n\n"
    
    # LOGICA PARA MOSTRAR INFORMACION DE EXCEDENTES APLICADOS
    if excedentes_aplicados > 0 and not complemento:
        mensaje += "EXCEDENTES APLICADOS\n\n"
        mensaje += f"Se aplicaron Q.{excedentes_aplicados:.2f} de tus pagos anteriores:\n"

        for detalle in detalle_excedentes:
            periodo_origen = detalle['periodo_origen']
            # Convertir periodo a formato legible
            if isinstance(periodo_origen, str) and "-" in periodo_origen:
                try:
                    ano, mes = periodo_origen.split("-")
                    mes_numero = int(mes)
                    mes_nombre = MESES_ES.get(mes_numero, f"Mes {mes}")
                    periodo_origen = f"{mes_nombre} de {ano}"
                except Exception:
                    pass
            
            mensaje += f"• Q.{detalle['monto_aplicado']:.2f} de tu excedente del período {periodo_origen}\n"
        
        mensaje += f"\nMonto original requerido: Q.{monto_original:.2f}\n"
        mensaje += f"Después de aplicar excedentes: Q.{monto_original - excedentes_aplicados:.2f}\n\n"


    # Para pagos complementarios, mostrar el progreso
    if complemento:
        mensaje += "¡ACTUALIZACIÓN DE PAGO COMPLEMENTARIO!\n\n"
        
        if estado == "exitosa" and faltante == 0:
            mensaje += "✅ TRANSACCIÓN COMPLETADA SATISFACTORIAMENTE\n\n"
            mensaje += f"Estado final: PAGO EXITOSO\n"
            mensaje += f"Modalidad de pago: {forma_pago}\n"
            mensaje += f"Período cubierto: {periodo}\n"
            mensaje += f"Monto total procesado: Q.{monto:.2f}\n\n"
            mensaje += "Resumen del proceso:\n"
            mensaje += "• Pago inicial recibido con faltante\n"
            mensaje += "• Pago complementario procesado exitosamente\n"
            mensaje += "• Cuenta cerrada y saldada completamente\n"
            
            if excedente > 0:
                mensaje += f"• Excedente generado: Q.{excedente:.2f}\n"
                
            if mora_aplicada:
                mensaje += "• Mora aplicada por atraso en el pago\n"

        elif estado == "pendiente_confirmacion" or estado == "espera_confirmacion":
            # Complementario completado pero pendiente de confirmacion
            mensaje += "✅ COMPLEMENTO COMPLETADO - PENDIENTE CONFIRMACIÓN\n\n"
            mensaje += f"Estado actual: {estado_desc}\n"
            mensaje += f"Modalidad de pago: {forma_pago}\n"
            mensaje += f"Período cubierto: {periodo}\n" 
            mensaje += f"Monto total procesado: Q.{monto:.2f}\n\n"
            mensaje += "📋 Resumen del proceso:\n"
            mensaje += "• Pago inicial recibido con faltante\n"
            mensaje += "• Pago complementario procesado exitosamente\n"
            mensaje += "• Monto total completado\n"
            mensaje += f"🔍 PENDIENTE: Confirmación de fondos para {forma_pago}\n"
            mensaje += "La transacción será marcada como exitosa una vez sean confirmados los fondos\n"
            
            if excedente > 0:
                mensaje += f"• Excedente generado: Q.{excedente:.2f}\n"
                
        else:
            mensaje += f"Estado: {estado_desc}\n"
            mensaje += f"Modalidad de pago: {forma_pago}\n"
            mensaje += f"Período: {periodo}\n"
            mensaje += f"Monto acumulado: Q.{monto:.2f}\n"
            
            if faltante > 0:
                mensaje += f"\n⏳ Pago complementario parcial. Faltante restante: Q.{faltante:.2f}\n"
                
    else:
        # Lógica original para pagos no complementarios
        mensaje += f"Estado: {estado_desc}\n"
        mensaje += f"Modalidad de pago: {forma_pago}\n"
        mensaje += f"Período registrado: {periodo}\n"
        mensaje += f"Monto de pago: Q.{monto:.2f}\n\n"

        # Casos especiales para excedentes
        if estado == "espera_acreditacion":
            if excedente > 0:
                mensaje += "PAGO EXITOSO CON EXCEDENTE\n\n"
                mensaje += f"La cuota del período {periodo} ha sido cubierta satisfactoriamente.\n"
                if excedentes_aplicados > 0:
                    mensaje += f"Se utilizaron Q.{excedentes_aplicados:.2f} de tus excedentes previos.\n"
                mensaje += f"Se detectó un excedente adicional de Q.{excedente:.2f} que se aplicará automáticamente a tu próximo pago.\n\n"

                if forma_pago.lower() == "efectivo":
                    mensaje += f"ESTADO: Esperando acreditación de saldo a favor.\n"
                    mensaje += "El excedente quedará disponible para pagos futuros.\n"
                else:
                    mensaje += f"PENDIENTE: Confirmación de fondos para: {forma_pago}\n"
                    mensaje += "Una vez confirmado los fondos, el excedente quedará disponible para uso futuro."
            else:
                # Caso donde se usaron excedentes para completar el pago exacto
                mensaje += "✅ PAGO COMPLETADO CON EXCEDENTES\n\n"
                mensaje += f"La cuota del período {periodo} ha sido cubierta satisfactoriamente utilizando tus excedentes previos.\n"
                if forma_pago.lower() != "efectivo":
                    mensaje += f"🔍 PENDIENTE: Confirmación de fondos para {forma_pago}\n"
        
        # Logica especifica para espera_acreditacion (SIN MENCIONAR EXCEDENTES)
        elif estado == "espera_acreditacion":
            mensaje += "PENDIENTE: Confirmación de fondos\n\n"
            mensaje += f"La cuota del período {periodo} ha sido procesada correctamente.\n"
            mensaje += f"Estado del pago: En espera de confirmación de fondos para {forma_pago}\n\n"
            mensaje += "Detalles: \n"
            mensaje += f"-Modalidad de pago: {forma_pago}\n"
            mensaje += f"-Monto procesado: Q.{monto:.2f}\n"
            mensaje += f"-Período cubierto: {periodo}\n\n"
            mensaje += "La transacción será confirmada una vez se verifiquen los fondos.\n"

            if excedente > 0:
                mensaje += f"Excedente detectado: Q.{excedente:.2f} (disponible tras confirmación)."

        # Estados principales
        if estado == "exitosa":
            if excedentes_aplicados > 0:
                    mensaje += "✅ PAGO COMPLETADO CON EXCEDENTES\n\n"
                    mensaje += f"La cuota del período {periodo} ha sido cubierta satisfactoriamente utilizando tus excedentes previos."
            else:
                mensaje += "✅ PAGO EXITOSO\n\n"
                mensaje += f"La cuota del período {periodo} ha sido cubierta satisfactoriamente."

            if excedente > 0:
                mensaje += f"\n Excedente detectado: Q.{excedente:.2f}. Este saldo se aplicara automaticamente a tu proximo pago"

            if mora_aplicada:
                mensaje += "\nNota: Se aplicó mora adicional por atraso."

        elif    estado == "espera_confirmacion":
            mensaje += "⏳ Pago pendiente de confirmación.\n"
            mensaje += "Esta modalidad requiere validación de fondos antes de ser considerada exitosa."
            if excedentes_aplicados > 0:
                mensaje += f"Se aplicaron Q.{excedentes_aplicados:.2f} de tus excedentes previos."
            if mora_aplicada:
                mensaje += "\nNota: Se aplicó mora adicional por atraso."

        elif estado == "pendiente":
            mensaje += "⏳ Pago pendiente."
            if excedentes_aplicados > 0:
                mensaje += f"\nSe aplicaron Q.{excedentes_aplicados:.2f} de tus excedentes previos"

        elif estado in ["fallida", "rechazada"]:
            mensaje += "❌ Pago rechazado."

        elif estado == "espera_complemento":
            # Detectar si también requiere confirmación de fondos
            TIPOS_REQUIEREN_CONFIRMACION = {'Cheque Propio', 'Cheque Ajeno', 'Cheque Exterior', 'Por Definir'}
            requiere_confirmacion = forma_pago in TIPOS_REQUIEREN_CONFIRMACION

            mensaje += "⚠️ Pago recibido parcialmente. Se requiere complemento para completar el período."

            if excedentes_aplicados > 0:
                mensaje += f"\nSe aplicaron Q.{excedentes_aplicados:.2f} de tus excedentes previos, pero aún resta un faltante de Q.{faltante:.2f}."

            if requiere_confirmacion:
                mensaje += f"\n IMPORTANTE: Adicionalmente, este tipo de pago: ({forma_pago}) está sujeto a confirmación de fondos."
                mensaje += "\n   • La confirmación final ocurrirá una vez completado el monto total"

        else:
            mensaje += f"Estado del pago: {estado_desc}."

        # Mostrar Excedente / faltante solo si no se manejo arriba
        if estado not in ["espera_acreditacion", "exitosa"] or (estado == "exitosa" and excedentes_aplicados == 0):
            if faltante > 0:
                mensaje += f"\n⚠️ Faltante detectado: Q.{faltante:.2f}."
            if excedente > 0:
                mensaje += f"\n💰 Excedente detectado: Q.{excedente:.2f}."

    return mensaje  