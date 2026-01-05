from django.apps import AppConfig
from django.conf import settings
import logging

logger = logging.getLogger("email_security")


class BoletasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'boletas'


    def ready(self):
        # Importar señales aquí para asegurarse de que se registren al iniciar la aplicación
        # Esto asegura que las señales se registren cuando la aplicación esté lista
        import boletas.signals
        from .services.email_ingestor.email_ingestor import validar_configuracion_email

        try:
            validar_configuracion_email()
        except Exception as e:
            if not settings.DEBUG:
                logger.error(f"Error de configuracion de email: {e}")
            else:
                raise
        
