import hashlib
from boletas.models import BoletaSandbox

def calculate_file_hash(file_obj) -> str:
    """
    Calcula el hash SHA-256 de un archivo abierto (file-like object).
    Se utiliza para detectar duplicados después del proceso seguro.
    """

    sha256 = hashlib.sha256()
    for chunk in iter(lambda: file_obj.read(4096), b""):
        sha256.update(chunk)
    file_obj.seek(0) # Regresar puntero para no corromper la lectura posterior
    return sha256.hexdigest()


def calculate_bytes_hash(data: bytes) -> str:
    """
    Calcula hash SHA-256 directamente desde bytes.
    """
    return hashlib.sha256(data).hexdigest()


def is_duplicate_hash(hash_value: str, current_id=None) -> bool:
    """
    Verifica si ya existe un registro en el sandbox con el mismo hash.
    Ignora el ID actual para evitar falsos positivos.
    """
    qs = BoletaSandbox.objects.filter(hash_image=hash_value)
    if current_id:
        qs = qs.exclude(id=current_id)
    return qs.exists()


