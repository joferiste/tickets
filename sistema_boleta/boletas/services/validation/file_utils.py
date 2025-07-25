# boletas/services/validation/file_utils.py
import os
import uuid
from django.conf import settings
from django.core.files.base import ContentFile

def generate_safe_filename(extension=".jpg") -> str:
    """
    Genera un nombre único y seguro para un archivo.
    Siempre usa UUID y extensión controlada (.jpg por defecto).
    """
    safe_name = f"{uuid.uuid4().hex}{extension}"
    return safe_name


def get_secure_upload_path(folder_name="sandbox_boletas") -> str:
    """
    Devuelve la ruta segura para subir archivos, asegurando que esté dentro de MEDIA_ROOT.
    """
    upload_path = os.path.join(settings.MEDIA_ROOT, folder_name)

    # Crear carpeta si no existe
    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)

    return upload_path


def save_image_to_disk(image_bytes: bytes, folder_name="sandbox_boletas") -> str:
    """
    Guarda una imagen (ya procesada) en disco con nombre seguro.
    Devuelve la ruta relativa para Django.
    """
    filename = generate_safe_filename(".jpg")
    secure_path = get_secure_upload_path(folder_name)
    full_path = os.path.join(secure_path, filename)

    with open(full_path, "wb") as f:
        f.write(image_bytes)

    # Devolver ruta relativa para Django ImageField
    relative_path = os.path.join(folder_name, filename)
    return relative_path
