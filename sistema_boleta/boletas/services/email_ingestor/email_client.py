import imaplib
import smtplib
import logging
import socket
from contextlib import contextmanager
from django.core.cache import cache
from django.conf import settings
from datetime import timedelta

# Configurar logging seguro (sin exponer datos sensibles)
logger = logging.getLogger('email_security')

class EmailConnectionError(Exception):
    """Excepcion personalizada para errores de conexion de Email"""
    pass


class EmailSecurityError(Exception):
    """Excepcion para problemas de seguridad en email"""
    pass


def verificar_rate_limit(ip_address=None):
    """
        Verificar si se excedio el limite de intentos de conexión.
        Protege contra ataques de fuerza bruta.
    """

    cache_key = f'email_attempts_{ip_address or "default"}'
    attempts = cache.get(cache_key, 0)

    max_attempts = getattr(settings, 'EMAIL_MAX_ATTEMPTS', 5)

    if attempts > max_attempts:
        logger.warning(f"[SEGURIDAD] Limites de intentos excedidos para {ip_address or 'sistema'}")
        raise EmailSecurityError(
            "Se excedio el limite de intentos de conexión. "
            "Intente nuevamente en 15 minutos."
        )
    
    # Incrementar contador 
    cache.set(cache_key, attempts + 1, timeout=900) # 15 minutos
    return True


def limpiar_rate_limit(ip_address=None):
    """Limpiar el contador de intentos despues de conexion exitosa"""
    cache_key = f'email_attempts_{ip_address or "default"}'
    cache.delete(cache_key)


@contextmanager
def connect_imap(timeout=30):
    """
    Context Manager para conexion IMAP segura.
    Asegura que la conexion SIEMPRE se cierre, incluso con errores.

    Uso:
        with connect_imap() as mail:
            mail.select('INBOX')
            #... OPERACIONES
        # La conexion se cierra automaticamente aqui
    """

    mail = None
    
    try:
        # Verificar rate limit
        verificar_rate_limit()

        # Validar configuracion
        if not all([
            settings.IMAP_SERVER,
            settings.EMAIL_USERNAME,
            settings.EMAIL_PASSWORD
        ]):
            logger.error("[SEGURIDAD] Configuracion IMAP imcompleta")
            raise EmailConnectionError("Configuracion de email incompleta")
        
        # Establecer timeout para evitar conexiones colgadas
        socket.setdefaulttimeout(timeout)

        # Conectar con SSL/TLS
        if settings.IMAP_USE_SSL:
            mail = imaplib.IMAP4_SSL(
                settings.IMAP_SERVER,
                settings.IMAP_PORT,
                timeout=timeout
            )
        else:
            # No recomendado, pero soportado
            logger.warning("[SEGURIDAD] Conexion IMAP sin SSL - No recomendado")
            mail = imaplib.IMAP4(settings.IMAP_SERVER, settings.IMAP_PORT)

        # Login con manejo de errores especificos
        try:
            mail.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            logger.info("[EMAIL] Conexion IMAP establecido correctamente")

            # Limpiar rate limit despues de login exitoso
            limpiar_rate_limit()
        
        except imaplib.IMAP4.error as e:
            error_msg = str(e).lower()

            if 'authentication failed' in error_msg or 'invalid credentials' in error_msg:
                logger.error('[SEGURIDAD] Credenciales IMAP inválidas')
                raise EmailSecurityError("Credenciales de email inválidas")
            else:
                logger.error(f"[EMAIL] Error de login IMAP: {type(e).__name__}")
                raise EmailConnectionError(f"Error de autenticación: {type(e).__name__}")
            
        # yield para usar el context manager
        yield mail

    except socket.timeout:
        logger.error("[EMAIL] Timeout en conexión IMAP")
        raise EmailConnectionError("Timeout de conexión al servidor de email")
        
    except socket.gaierror:
        logger.error("[EMAIL] Error de DNS al resolver servidor IMAP")
        raise EmailConnectionError("No se pudo resolver el servidor de email")
        
    except Exception as e:
        logger.error(f"[EMAIL] Error inesperado en IMAP: {type(e).__name__}")
        raise EmailConnectionError(f"Error de conexión: {type(e).__name__}")
        
    finally:
        # CRÍTICO: Siempre cerrar la conexión
        if mail is not None:
            try:
                mail.logout()
                logger.info("[EMAIL] Conexión IMAP cerrada correctamente")
            except Exception as e:
                logger.warning(f"[EMAIL] Error al cerrar IMAP: {type(e).__name__}")
        
        # Restaurar timeout por defecto
        socket.setdefaulttimeout(None)


@contextmanager
def connect_smtp(timeout=30):
    """
    Context manager para conexión SMTP segura.
    
    Uso:
        with connect_smtp() as smtp:
            smtp.send_message(msg)
        # La conexión se cierra automáticamente aquí
    """
    smtp = None
    
    try:
        # Verificar rate limit
        verificar_rate_limit()
        
        # Validar configuración
        if not all([
            settings.EMAIL_HOST,
            settings.EMAIL_HOST_USER,
            settings.EMAIL_HOST_PASSWORD
        ]):
            logger.error("[SEGURIDAD] Configuración SMTP incompleta")
            raise EmailConnectionError("Configuración de email incompleta")
        
        # Establecer timeout
        socket.setdefaulttimeout(timeout)
        
        # Conectar con SSL/TLS
        if settings.EMAIL_USE_SSL:
            smtp = smtplib.SMTP_SSL(
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
                timeout=timeout
            )
        else:
            smtp = smtplib.SMTP(
                settings.EMAIL_HOST,
                settings.EMAIL_PORT,
                timeout=timeout
            )
            # Intentar STARTTLS si no es SSL directo
            try:
                smtp.starttls()
            except Exception:
                logger.warning("[SEGURIDAD] No se pudo establecer STARTTLS")
        
        # Login
        try:
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            logger.info("[EMAIL] Conexión SMTP establecida correctamente")
            
            # Limpiar rate limit
            limpiar_rate_limit()
            
        except smtplib.SMTPAuthenticationError:
            logger.error("[SEGURIDAD] Credenciales SMTP inválidas")
            raise EmailSecurityError("Credenciales de email inválidas")
        
        yield smtp
        
    except socket.timeout:
        logger.error("[EMAIL] Timeout en conexión SMTP")
        raise EmailConnectionError("Timeout de conexión al servidor SMTP")
        
    except Exception as e:
        logger.error(f"[EMAIL] Error inesperado en SMTP: {type(e).__name__}")
        raise EmailConnectionError(f"Error de conexión SMTP: {type(e).__name__}")
        
    finally:
        # CRÍTICO: Siempre cerrar la conexión
        if smtp is not None:
            try:
                smtp.quit()
                logger.info("[EMAIL] Conexión SMTP cerrada correctamente")
            except Exception as e:
                logger.warning(f"[EMAIL] Error al cerrar SMTP: {type(e).__name__}")
        
        socket.setdefaulttimeout(None)


def verificar_conexion_imap():
    """
    Verifica que la conexión IMAP funcione correctamente.
    Útil para health checks.
    """
    try:
        with connect_imap(timeout=10) as mail:
            status, _ = mail.select("INBOX", readonly=True)
            return status == 'OK'
    except Exception as e:
        logger.error(f"[EMAIL] Verificación IMAP falló: {type(e).__name__}")
        return False


def verificar_conexion_smtp():
    """
    Verifica que la conexión SMTP funcione correctamente.
    Útil para health checks.
    """
    try:
        with connect_smtp(timeout=10) as smtp:
            # NOOP es un comando que no hace nada, solo verifica la conexión
            status = smtp.noop()
            return status[0] == 250
    except Exception as e:
        logger.error(f"[EMAIL] Verificación SMTP falló: {type(e).__name__}")
        return False