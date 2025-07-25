import email
from email.header import decode_header
import email.message
import email.utils
from boletas.models import BoletaSandbox
from .email_client import connect_imap
from django.core.files.base import ContentFile
import imaplib
from boletas.services.validation.validation import validar_boleta_sandbox

def limpiar_texto(texto):
    """ Limpiar texto codificado del asunto """
    decoded = decode_header(texto)
    asunto = ""
    for fragment, encoding in decoded:
        if isinstance(fragment, bytes):
            fragment = fragment.decode(encoding or 'utf-8', errors='ignore')
        asunto += fragment
    return asunto.strip()


def procesar_correos():
    imap = connect_imap()
    if not imap:
        print("[ERROR] No se puede conectar a IMAP")
        return 0
    
    imap.select("INBOX")
    status, mensajes = imap.search(None, 'UNSEEN') # Correos no leidos
    if status != "OK":
        print("[ERROR] No se pudieron buscar correos.")
        return 0
    
    ids = mensajes[0].split()
    print("[DEBUG] Correos no leidos encontrados: {len(ids)}")
    
    count = 0
    for num in ids:
        _, data = imap.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Extraer remitente
        remitente = email.utils.parseaddr(msg.get('From'))[1]
        asunto = limpiar_texto(msg.get("Subject", ""))
        cuerpo = ""
        archivo = None
        archivo_nombre = ""

        if msg.is_multipart():
            for parte in msg.walk():
                content_type = parte.get_content_type()
                dispo = str(parte.get("Content-Disposition", ""))

                if content_type == "text/plain" and "attachment" not in dispo:
                    cuerpo += parte.get_payload(decode=True).decode(errors='ignore')
                elif ("attachment" in dispo or parte.get_filename()):
                    archivo = parte.get_payload(decode=True)
                    archivo_nombre = parte.get_filename() or f"imagen_{count}.jpg"
        else:
            cuerpo = msg.get_payload(decode=True).decode(errors="ignore")

        if BoletaSandbox.objects.filter(remitente=remitente, asunto=asunto).exists():
            print(f"[INFO] Correo duplicado de {remitente} con asunto {asunto}, omitido.")
            continue

        # Crear boleta sandbox
        sandbox = BoletaSandbox(
            remitente=remitente,
            asunto=asunto,
            mensaje=cuerpo.strip(),
        )

        if archivo:
            if not archivo_nombre: # Si Gmail no envia nombre
                archivo_nombre = f"imagen_{count}.jpg" # Nombre por defecto
            sandbox.imagen.save(archivo_nombre, ContentFile(archivo), save=False)

        # Agregar metadata útil
        metadata = {
            "fecha_original": msg.get("Date"),
            "message_id": msg.get("Message-ID"),
            "mime_version": msg.get("MIME-Version"),
            "content_type": msg.get("Content-Type"),
            "encoding": msg.get("Content-Transfer-Encoding"),
        }
        sandbox.metadata = metadata

        sandbox.save()

        validar_boleta_sandbox(sandbox)

        # Marcar como leido
        imap.store(num, '+FLAGS', '\\Seen')

        count += 1

    imap.logout()
    return count