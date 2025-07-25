import bleach
from django.utils.html import escape

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
