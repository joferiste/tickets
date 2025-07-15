import os
from PIL import Image
from boletas.models import Boleta
from negocios.models import Negocio


def validar_boleta_sandbox(boleta_sandbox):
    errors = []

    # 1. Validar si un email esta asociado a un negocio
    negocio = Negocio.objects.filter(email__iexact=boleta_sandbox.email).first()
    if not negocio:
        errors.append("Remitente no asociado a ningun negocio registrado.")

    # 2. Validacion del archivo de imagen
    extensiones_permitidas = ['.jpg', '.jpeg', '.png']
    extensiones = os.path.splitext(boleta_sandbox.imagen.name)[1].lower()
    if extensiones not in extensiones_permitidas:
        errors.append("Extension de archivo no permitida. Se aceptan unicamente .jpg, .jpeg, .png")
    elif boleta_sandbox.image.size > 5 * 1024 * 1024:
        errors.append("La imagen supera el limite de 5MB permitido.")
    else:
        try:
            img = Image.open(boleta_sandbox.imagen)
            img.verify()
        except Exception:
            errors.append("El archivo cargado no es una imagen valida.")


    # 3. Validar que el mensaje tenga contenido
    if not boleta_sandbox.mensaje or len(boleta_sandbox.mensaje.strip()) == 0:
        errors.append("El mensaje del correo esta vacio.")

    
    # 4. Validar duplicados (Si ya existe una boleta con ese numero para el negocio)
    if negocio and boleta_sandbox.numeroBoleta:
        if Boleta.objects.filter(numeroBoleta = boleta_sandbox.numeroBoleta, negocio=negocio).exists():
            errors.append("Ya existe una boleta con este numero para el negocio indicado.")

    # Resultado
    if errors:
        boleta_sandbox.estado_validacion = "Rechazada"
        boleta_sandbox.comentarios_validacion = "; ".join(errors)
    else:
        boleta_sandbox.estado_validacion = "Exitosa"
        boleta_sandbox.comentarios_validacion = "Validacion tecnica exitosa"

    boleta_sandbox.save()
    return boleta_sandbox.estado_validacion == 'Aprobada'