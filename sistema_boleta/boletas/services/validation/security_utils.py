import bleach
from django.utils.html import escape
from boletas.models import BoletaSandbox
from datetime import timedelta
from django.utils.timezone import now

# Lista de etiquetas y atributos permitidos (ninguno en este caso)
ALLOWED_TAGS = []
ALLOWED_ATRIBUTES = {}

def sanitize_text(text: str) -> str:
    """
    Limpia un texto para prevenir inyecciones HTML o JS.
    - Escapa caracteres peligrosos.
    - Elimina cualquier etiqueta HTML.
    """
    
    if not text:
        return ""
    
    # 1. Escape basico (por seguridad extra)
    safe_text = escape(text)

    # 2. Sanitizacion profunda con bleach (quita etiquetas peligrosas)
    clean_text = bleach.clean(
        safe_text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATRIBUTES,
        strip=True
    )

    return clean_text


def is_duplicate_message(message_id: str, current_id:None) -> bool:
    qs = BoletaSandbox.objects.filter(message_id=message_id)
    if current_id:
        qs = qs.exclude(id=current_id)
    return qs.exists()


def is_recent_duplicate(remitente: str, hash_value: str, minutes: int = 10) -> bool:
    time_limit = now() - timedelta(minutes=minutes)
    return BoletaSandbox.objects.filter(
        remitente=remitente,
        hash_image=hash_value,
        fecha_recepcion__gte=time_limit
    )