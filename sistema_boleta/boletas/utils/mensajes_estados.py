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
    #comentarios = resultado_pago.get("comentarios", [])

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
            mensaje += "   La transacción será marcada como exitosa una vez sean confirmados los fondos\n"
            
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

        # Estados principales
        if estado == "exitosa":
            mensaje += "✅ Pago satisfactorio."
            if mora_aplicada:
                mensaje += "\nNota: Se aplicó mora adicional por retraso."
        elif estado == "pendiente_confirmacion" or estado == "espera_confirmacion":
            mensaje += "⏳ Pago pendiente de confirmación.\n"
            mensaje += "Esta modalidad requiere validación de fondos antes de ser considerada exitosa."
            if mora_aplicada:
                mensaje += "\nNota: Se aplicó mora adicional por atraso."
        elif estado == "pendiente":
            mensaje += "⏳ Pago pendiente."
        elif estado in ["fallida", "rechazada"]:
            mensaje += "❌ Pago rechazado."
        elif estado == "espera_complemento":
            # Detectar si también requiere confirmación de fondos
            TIPOS_REQUIEREN_CONFIRMACION = {'Cheque Propio', 'Cheque Ajeno', 'Cheque Exterior', 'Por Definir'}
            requiere_confirmacion = forma_pago in TIPOS_REQUIEREN_CONFIRMACION

            mensaje += "⚠️ Pago recibido parcialmente. Se requiere complemento para completar el período."

            if requiere_confirmacion:
                mensaje += f"\n IMPORTANTE: Adicionalmente, este tipo de pago: ({forma_pago}) está sujeto a confirmación de fondos."
                mensaje += "\n   • La confirmación final ocurrirá una vez completado el monto total"

        else:
            mensaje += f"Estado del pago: {estado_desc}."

        # Excedente / faltante para pagos no complementarios
        if faltante > 0:
            mensaje += f"\n⚠️ Faltante detectado: Q.{faltante:.2f}."
        if excedente > 0:
            mensaje += f"\n💰 Excedente detectado: Q.{excedente:.2f}."

    # Comentarios adicionales
    #if comentarios:
    #    mensaje += "\n\n📝 Detalles adicionales:\n- " + "\n- ".join(comentarios)

    return mensaje  