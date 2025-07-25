import os
import uuid
from io import BytesIO
from PIL import Image, ImageOps
from PIL import ExifTags
from django.core.files.base import ContentFile

# Configuracion segura
MAX_FILE_SIZE_MB = 4
MAX_RESOLUTION = (2000, 2000) # Máximo 2000x2000px
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']

def process_and_sanitize_image(uploaded_image, email_provider=None):
    """
    Procesa una imagen cargada aplicando validaciones y medidas anti-exploit:
    1. Valida extensión permitida
    2. Verifica estructura real de imagen
    3. Convierte a formato seguro JPEG
    4. Elimina metadatos EXIF
    5. Ajusta tamaño (si excede resolución o tamaño máximo)
    6. Retorna un diccionario con nombre y contenido seguro
    email_provider: gmail, hotmail, outlook, etc.
    """
    
    # Manejar tanto archivos directos como FieldFile de Django
    if hasattr(uploaded_image, 'file'):
        # Es un FieldFile (ImageField/FileField de Django)
        file_obj = uploaded_image.file
        file_name = uploaded_image.name
    elif hasattr(uploaded_image, 'name') and hasattr(uploaded_image, 'read'):
        # Es un archivo cargado directamente
        file_obj = uploaded_image
        file_name = uploaded_image.name
    else:
        raise ValueError("El objeto proporcionado no es un archivo válido")


    # Validar extensión
    extension = os.path.splitext(file_name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Extension no permitida. Unicamente aceptadas: jpg, jpeg y png")
    

    # Abrir imagen y verificar seguridad
    try:
        # Asegurar que estamos al inicio del archivo
        uploaded_image.seek(0)
        img = Image.open(file_obj)
        img.verify() #Analiza estructura interna
    except Exception as e:
        raise ValueError(f"Archivo no es imagen valida o esta corrupta: {str(e)}")
    

    # Reabrir (img.verify cierra el archivo)
    uploaded_image.seek(0)
    img = Image.open(file_obj)

    # Convertir a formato seguro (JPEG) y quitar EXIF
    img = img.convert("RGB") # Obliga RGB
    data = list(img.getdata()) # Quita EXIF
    img_without_exif = Image.new(img.mode, img.size)
    img_without_exif.putdata(data)


    # Redimensionar si excede resolucion maxima
    if img_without_exif.width > MAX_RESOLUTION[0] or img_without_exif.height > MAX_RESOLUTION[1]:
        img_without_exif.thumbnail(MAX_RESOLUTION)


    # Guardar en buffer
    buffer = BytesIO()
    img_without_exif.save(buffer, format="JPEG", quality=95)
    buffer.seek(0)


    # Si sigue siendo muy grande, se aplica compresion extra
    if buffer.getbuffer().nbytes > MAX_FILE_SIZE_MB * 1024 * 1024:
        buffer = BytesIO()
        img_without_exif.save(buffer, format="JPEG", quality=90)
        buffer.seek(0)

    
    # Nombre seguro (UUID) y extension forzada a .jpg
    safe_name = f"{uuid.uuid4().hex}.jpg"


    return ContentFile(buffer.read()), safe_name
