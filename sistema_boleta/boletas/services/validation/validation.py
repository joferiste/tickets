import os
import hashlib
from io import BytesIO
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.html import escape
from boletas.models import Boleta, BoletaSandbox
from negocios.models import Negocio
import bleach
import gc
from .image_utils import process_and_sanitize_image
from .security_utils import sanitize_text
from .hash_utils import calculate_file_hash, is_duplicate_in_sandbox

def validar_boleta_sandbox(boleta_sandbox) -> bool:
    """
    Valida técnica y sanitariamente un registro en BoletaSandbox.
    Retorna True si la validación es exitosa, False si falla.
    """

    print(f"[INFO] Iniciando validación para sandbox ID={boleta_sandbox.id}, remitente={boleta_sandbox.remitente}")
    errors = []
    file_hash = None # Se inicializa para evitar NameError
    metadata = dict(boleta_sandbox.metadata or {})


    # 1. Sanitizar texto contra inyecciones
    boleta_sandbox.asunto = sanitize_text(boleta_sandbox.asunto or "")
    boleta_sandbox.mensaje = sanitize_text(boleta_sandbox.mensaje or "")
    print("[INFO] Mensaje limpiado para prevenir inyecciones.")


    # 2. Validar si un email esta asociado a un negocio
    print("[INFO] Validando asociación con negocio...")
    negocio = Negocio.objects.filter(email__iexact=boleta_sandbox.remitente).first()
    if not negocio:
        errors.append("Remitente no asociado a ningun negocio registrado.")
        print("[WARN] Negocio no detectado para el remitente.")
    else:
        metadata["negocio"] = negocio.nombre
        metadata["negocio_id"] = negocio.idNegocio
        metadata["negocio_email"] = negocio.email


    # 3. Validar que exista imagen (obligatoria)
    if not boleta_sandbox.imagen or not boleta_sandbox.imagen.name:
            errors.append("Debe de existir una imagen de boleta para procesar el pago.")
            print("[ERROR] Correo sin imagen.")
    else:
        try:
            if not boleta_sandbox.imagen or not boleta_sandbox.imagen.name:
                print("[WARN] No hay imagen para procesar..")
                return False
        
            ruta_original = boleta_sandbox.imagen.path # Se usa path
            print(f"[INFO] Procesando imagen: {ruta_original}")

            #3 Procesar imagen y generar version segura
            safe_image_bytes, safe_name = process_and_sanitize_image(boleta_sandbox.imagen.file)
            print(f"[INFO] Imagen procesada. Nuevo nombre: ", safe_name)

            # Cerrar todos los handles del archivo original
            if hasattr(boleta_sandbox.imagen.file, 'close'):
                boleta_sandbox.imagen.file.close()

            # Desasignar la imagen original del modelo (Sin save=False)
            boleta_sandbox.imagen.delete(save=True) # Esto cierra handles y limpia BD

            # Forzar garbage collection para liberar handles
            gc.collect()

            #3.1.1 Eliminar archivo original del disco
            try:
                if os.path.exists(ruta_original):
                    os.remove(ruta_original)
                    print("[INFO] Imagen original borrada", ruta_original)
                else:
                    print(f"[WARN] Archivo original no encontrado: {ruta_original}")
            except PermissionError as pe:
                print(f"[WARN] No se puede eliminar archivo original: {pe}")


            # Asignar nueva imagen procesada
            boleta_sandbox.imagen.save(safe_name, safe_image_bytes, save=True)

            print(f"[SUCCESS] Nueva imagen guardada: {boleta_sandbox.imagen.name}")
            print(f"Nombre del archivo: {boleta_sandbox.imagen.name}")
            print(f"[INFO] Ruta final: {boleta_sandbox.imagen.path}")
            


            #3.3 Calcular el hash sobre version segura
            file_hash = calculate_file_hash(boleta_sandbox.imagen)

            #3.4 Validar duplicado 
            if is_duplicate_in_sandbox(file_hash, current_id=boleta_sandbox.id):
                errors.append("Archivo duplicado. Ya existe en el sandbox")

            metadata["hash"] = file_hash
        
        except Exception as e:
            errors.append(f"Error procesando la imagen {str(e)}")


    # 4. Validación de mensaje (opcional, solo info)
    if not boleta_sandbox.mensaje or len(boleta_sandbox.mensaje.strip()) == 0:
        print("[INFO] Correo sin mensaje, solo imagen.")


    # Resultado de validacion
    if errors:
        boleta_sandbox.estado_validacion = "Rechazada"
        boleta_sandbox.comentarios_validacion = "; ".join(errors)
        boleta_sandbox.motivo_rechazo = "; ".join(errors)
        boleta_sandbox.es_valida = False
        print(f"[WARN] Validación rechazada: {errors}")
    else:
        boleta_sandbox.estado_validacion = "Exitosa"
        boleta_sandbox.comentarios_validacion = "Validación técnica exitosa."
        boleta_sandbox.es_valida = True
        print("[INFO] Validación exitosa.")

    boleta_sandbox.procesado = True
    boleta_sandbox.metadata = metadata
    boleta_sandbox.save()
    print("[INFO] Sandbox actualizado en base de datos.")

    return boleta_sandbox.es_valida