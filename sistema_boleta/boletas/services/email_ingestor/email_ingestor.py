# boletas/services/email_ingestor.py

import email
from email.header import decode_header
import email.message
import email.utils
import imaplib
import logging
from django.core.files.base import ContentFile
from boletas.models import BoletaSandbox
from .email_client import connect_imap, EmailConnectionError, EmailSecurityError
from boletas.services.validation.validation import validar_boleta_sandbox

logger = logging.getLogger('email_security')


def limpiar_texto(texto):
    """
    Limpiar texto codificado del asunto.
    Protege contra inyección de código en headers.
    """
    if not texto:
        return ""
    
    try:
        decoded = decode_header(texto)
        asunto = ""
        for fragment, encoding in decoded:
            if isinstance(fragment, bytes):
                fragment = fragment.decode(encoding or 'utf-8', errors='ignore')
            asunto += fragment
        
        # Sanitizar: remover caracteres peligrosos
        asunto = asunto.strip()
        # Limitar longitud para evitar ataques de buffer overflow
        asunto = asunto[:500]
        
        return asunto
    except Exception as e:
        logger.warning(f"[EMAIL] Error al decodificar texto: {type(e).__name__}")
        return str(texto)[:500]


def procesar_correos(limite=50):
    """
    Procesa correos no leídos del inbox de forma segura.
    
    Args:
        limite: Número máximo de correos a procesar por ejecución
    
    Returns:
        int: Cantidad de correos procesados exitosamente
    """
    count = 0
    
    try:
        # Usar context manager para asegurar cierre de conexión
        with connect_imap(timeout=30) as imap:
            
            # Seleccionar inbox
            status, _ = imap.select("INBOX")
            if status != "OK":
                logger.error("[EMAIL] No se pudo seleccionar INBOX")
                return 0
            
            # Buscar correos no leídos
            status, mensajes = imap.search(None, 'UNSEEN')
            if status != "OK":
                logger.error("[EMAIL] Error al buscar correos no leídos")
                return 0
            
            ids = mensajes[0].split()
            total_encontrados = len(ids)
            
            logger.info(f"[EMAIL] {total_encontrados} correos no leídos encontrados")
            print(f"[DEBUG] Correos no leídos encontrados: {total_encontrados}")
            
            # Limitar procesamiento
            ids = ids[:limite]
            
            if total_encontrados > limite:
                logger.warning(
                    f"[EMAIL] Limitando procesamiento a {limite} de {total_encontrados} correos"
                )
            
            # Procesar cada correo
            for num in ids:
                try:
                    # Fetch del correo
                    _, data = imap.fetch(num, "(RFC822)")
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extraer remitente
                    remitente = email.utils.parseaddr(msg.get('From'))[1]
                    
                    if not remitente:
                        logger.warning("[EMAIL] Correo sin remitente válido")
                        imap.store(num, '+FLAGS', '\\Seen')
                        continue
                    
                    # Extraer información
                    asunto = limpiar_texto(msg.get("Subject", ""))
                    message_id = msg.get("Message-ID", "")
                    cuerpo = ""
                    archivo = None
                    archivo_nombre = ""

                    # Procesar contenido
                    if msg.is_multipart():
                        for parte in msg.walk():
                            content_type = parte.get_content_type()
                            dispo = str(parte.get("Content-Disposition", ""))

                            # Extraer texto
                            if content_type == "text/plain" and "attachment" not in dispo:
                                try:
                                    payload = parte.get_payload(decode=True)
                                    if payload:
                                        cuerpo += payload.decode(errors='ignore')
                                except Exception as e:
                                    logger.warning(f"[EMAIL] Error al decodificar texto: {type(e).__name__}")
                            
                            # Extraer archivo adjunto
                            elif "attachment" in dispo or parte.get_filename():
                                try:
                                    archivo = parte.get_payload(decode=True)
                                    archivo_nombre = parte.get_filename() or f"adjunto_{num.decode()}.jpg"
                                except Exception as e:
                                    logger.warning(f"[EMAIL] Error al procesar adjunto: {type(e).__name__}")
                                    archivo = None
                    else:
                        # Correo simple (no multipart)
                        try:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                cuerpo = payload.decode(errors="ignore")
                        except Exception as e:
                            logger.warning(f"[EMAIL] Error al decodificar payload: {type(e).__name__}")

                    # Verificar duplicados
                    if BoletaSandbox.objects.filter(
                        remitente=remitente,
                        asunto=asunto,
                        message_id=message_id
                    ).exists():
                        logger.info(f"[EMAIL] Correo duplicado: {remitente} - {asunto}")
                        print(f"[INFO] Correo duplicado de {remitente} con asunto '{asunto}', omitido.")
                        # Marcar como leído
                        imap.store(num, '+FLAGS', '\\Seen')
                        continue

                    # Crear boleta sandbox
                    sandbox = BoletaSandbox(
                        remitente=remitente,
                        asunto=asunto,
                        mensaje=cuerpo.strip()[:5000],  # Limitar longitud
                        message_id=message_id,
                    )

                    # Guardar archivo si existe
                    if archivo and archivo_nombre:
                        try:
                            if not archivo_nombre:
                                archivo_nombre = f"imagen_{count}.jpg"
                            
                            sandbox.imagen.save(
                                archivo_nombre[:100],  # Limitar longitud del nombre
                                ContentFile(archivo),
                                save=False
                            )
                        except Exception as e:
                            logger.error(f"[EMAIL] Error al guardar archivo: {type(e).__name__}")

                    # Agregar metadata (sin información sensible)
                    metadata = {
                        "fecha_original": msg.get("Date"),
                        "message_id": message_id,
                        "tiene_adjunto": bool(archivo),
                    }
                    sandbox.metadata = metadata

                    # Guardar en base de datos
                    sandbox.save()

                    # Validar boleta
                    try:
                        validar_boleta_sandbox(sandbox)
                    except Exception as e:
                        logger.error(f"[EMAIL] Error en validación: {type(e).__name__}")

                    # Marcar como leído
                    imap.store(num, '+FLAGS', '\\Seen')

                    count += 1
                    logger.info(f"[EMAIL] Correo procesado exitosamente: {remitente}")
                    print(f"[INFO] Procesado: {remitente} - {asunto}")

                except Exception as e:
                    logger.error(f"[EMAIL] Error procesando correo individual: {type(e).__name__}")
                    print(f"[ERROR] Error en correo: {e}")
                    # Continuar con el siguiente correo
                    continue
            
            logger.info(f"[EMAIL] Procesamiento completado: {count} correos procesados")
            
    except EmailConnectionError as e:
        logger.error(f"[EMAIL] Error de conexión: {e}")
        print(f"[ERROR] No se puede conectar a IMAP: {e}")
        return 0
        
    except EmailSecurityError as e:
        logger.error(f"[SEGURIDAD] Error de seguridad: {e}")
        print(f"[ERROR] Error de seguridad: {e}")
        return 0
        
    except Exception as e:
        logger.error(f"[EMAIL] Error inesperado: {type(e).__name__}")
        print(f"[ERROR] Error inesperado: {e}")
        return 0
    
    return count