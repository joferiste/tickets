from django.db import transaction, IntegrityError
import os
import hashlib
from io import BytesIO
from PIL import Image
from django.conf import settings
from django.core.files.base import ContentFile
from boletas.models import Boleta, BoletaSandbox
from negocios.models import Negocio
import gc
from .image_utils import process_and_sanitize_image
from .security_utils import sanitize_text, is_duplicate_message, is_recent_duplicate
from .hash_utils import calculate_file_hash, is_duplicate_hash

def validar_boleta_sandbox(boleta_sandbox) -> bool:
    """
    Valida técnica y sanitariamente un registro en BoletaSandbox.
    Retorna True si la validación es exitosa, False si falla.
    """
    print(f"[INFO] Iniciando validación para sandbox ID={boleta_sandbox.id}, remitente={boleta_sandbox.remitente}")
    
    errors = []
    file_hash = None
    metadata = dict(boleta_sandbox.metadata or {})
    es_duplicado_hash = False  # Flag para saber si hay duplicado
    
    try:
        # 1. Sanitizar texto
        boleta_sandbox.asunto = sanitize_text(boleta_sandbox.asunto or "")
        boleta_sandbox.mensaje = sanitize_text(boleta_sandbox.mensaje or "")
        print("[INFO] Mensaje limpiado para prevenir inyecciones.")
        
        # 2. Validar negocio
        print("[INFO] Validando asociación con negocio...")
        negocio = Negocio.objects.filter(email__iexact=boleta_sandbox.remitente).first()
        if not negocio:
            errors.append("Remitente no asociado a ningun negocio registrado.")
            print("[WARN] Negocio no detectado para el remitente.")
        else:
            metadata["negocio"] = negocio.nombre
            metadata["negocio_id"] = negocio.idNegocio
            metadata["negocio_email"] = negocio.email
        
        # 3. Validar imagen
        if not boleta_sandbox.imagen or not boleta_sandbox.imagen.name:
            boleta_sandbox.estado_validacion = 'sin_imagen'
            boleta_sandbox.leido = True
            boleta_sandbox.save()
            print("[ERROR] Correo sin imagen.")
            return False
        
        # Procesar imagen
        ruta_original = boleta_sandbox.imagen.path
        print(f"[INFO] Procesando imagen: {ruta_original}")
        
        # Guardar info original
        original_filename = os.path.basename(ruta_original)
        original_hash = calculate_file_hash(boleta_sandbox.imagen)
        metadata["original_filename"] = original_filename
        metadata["original_hash"] = original_hash
        print(f"[INFO] Original -> filename={original_filename}, hash={original_hash}")
        
        # Procesar y sanitizar imagen
        safe_image_bytes, safe_name = process_and_sanitize_image(boleta_sandbox.imagen.file)
        print(f"[INFO] Imagen procesada. Nuevo nombre: {safe_name}")
        
        # Cerrar handles
        if hasattr(boleta_sandbox.imagen.file, 'close'):
            boleta_sandbox.imagen.file.close()
        
        # Eliminar imagen original
        boleta_sandbox.imagen.delete(save=False)
        gc.collect()
        
        # Eliminar del disco
        try:
            if os.path.exists(ruta_original):
                os.remove(ruta_original)
                print(f"[INFO] Imagen original borrada: {ruta_original}")
            else:
                print(f"[WARN] Archivo original no encontrado: {ruta_original}")
        except PermissionError as pe:
            print(f"[WARN] No se puede eliminar archivo original: {pe}")
        
        # Asignar nueva imagen SIN guardar aún
        boleta_sandbox.imagen.save(safe_name, safe_image_bytes, save=False)
        print(f"[SUCCESS] Nueva imagen preparada: {boleta_sandbox.imagen.name}")
        
        # Calcular hash de versión segura
        file_hash = calculate_file_hash(boleta_sandbox.imagen)
        metadata["safe_filename"] = boleta_sandbox.imagen.name
        metadata["safe_hash"] = file_hash
        print(f"[INFO] Seguro -> filename={boleta_sandbox.imagen.name}, hash={file_hash}")
        
        # 4. Validar mensaje
        if not boleta_sandbox.mensaje or len(boleta_sandbox.mensaje.strip()) == 0:
            print("[INFO] Correo sin mensaje, solo imagen.")
        
        # 5. Validar duplicado por message_id
        if boleta_sandbox.message_id and is_duplicate_message(boleta_sandbox.message_id, current_id=boleta_sandbox.id):
            errors.append("Correo duplicado. Este mensaje ya fue procesado.")
        
        # 6. Validar duplicado por hash_image
        if file_hash and is_duplicate_hash(file_hash, current_id=boleta_sandbox.id):
            errors.append("Archivo duplicado. Ya existe una boleta con esta imagen")
            es_duplicado_hash = True  # ⚠️ Marcar que hay duplicado
        
        # 7. Validar envío reciente
        if is_recent_duplicate(boleta_sandbox.remitente, file_hash, minutes=2):
            errors.append("Posible duplicado: misma imagen enviada en menos de 2 minutos.")
        
        # Resultado de validación
        if errors:
            boleta_sandbox.estado_validacion = "rechazada"
            boleta_sandbox.comentarios_validacion = "; ".join(errors)
            boleta_sandbox.motivo_rechazo = "; ".join(errors)
            boleta_sandbox.es_valida = False
            print(f"[WARN] Validación rechazada: {errors}")
        else:
            boleta_sandbox.estado_validacion = "exitosa"
            boleta_sandbox.comentarios_validacion = "Validación técnica exitosa."
            boleta_sandbox.es_valida = True
            print("[INFO] Validación exitosa.")
        
        boleta_sandbox.procesado = True
        boleta_sandbox.metadata = metadata
        
        # ⚠️ SI HAY DUPLICADO DE HASH, NO LO ASIGNES
        if not es_duplicado_hash:
            boleta_sandbox.hash_image = file_hash
        else:
            # Guardar info del hash en metadata pero NO en el campo
            metadata["hash_duplicado"] = file_hash
            metadata["razon_sin_hash"] = "Hash duplicado, no se guarda para evitar constraint violation"
            boleta_sandbox.metadata = metadata
            print("[WARN] Hash duplicado detectado, no se asigna al campo hash_image")
        
        # Guardar con transaction para rollback automático
        with transaction.atomic():
            boleta_sandbox.save()
            print("[INFO] Sandbox actualizado en base de datos.")
        
        return boleta_sandbox.es_valida
        
    except IntegrityError as ie:
        print(f"[ERROR] Error de integridad en BD: {str(ie)}")
        # Intentar guardar sin el hash problemático
        try:
            boleta_sandbox.hash_image = None  # Remover hash
            boleta_sandbox.estado_validacion = "rechazada"
            boleta_sandbox.motivo_rechazo = f"Error de integridad: {str(ie)}"
            boleta_sandbox.comentarios_validacion = f"Duplicado detectado: {str(ie)}"
            boleta_sandbox.es_valida = False
            boleta_sandbox.procesado = True
            boleta_sandbox.save()
            print("[INFO] Guardado sin hash debido a duplicado.")
        except Exception as e2:
            print(f"[ERROR] No se pudo guardar ni siquiera sin hash: {str(e2)}")
        return False
        
    except Exception as e:
        print(f"[ERROR] Error en validación: {str(e)}")
        try:
            boleta_sandbox.estado_validacion = "error"
            boleta_sandbox.comentarios_validacion = f"Error técnico: {str(e)}"
            boleta_sandbox.es_valida = False
            boleta_sandbox.procesado = True
            boleta_sandbox.save()
        except:
            pass
        return False