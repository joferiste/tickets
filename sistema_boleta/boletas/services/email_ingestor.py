import email
from email.header import decode_header
import email.message
import email.utils
from boletas.models import BoletaSandbox
from .email_client import connect_imap
from django.core.files.base import ContentFile
import imaplib

def limpiar_texto(texto):
    """ Limpiar texto codificado del asunto """
    decoded = decode_header(texto)
    asunto = ""
    for fragment, encoding in decoded:
        if isinstance(fragment, bytes):
            fragment = fragment.decode(encoding or 'utf-8', errors='ignore')
        asunto += fragment
    return asunto.trip()


def procesar_correos():
    imap = connect_imap()
    if not imap:
        return 0
    
    imap.select("INBOX")

    status, mensajes = imap.search(None, 'UNSEEN') # Correos no leidos
    if status != "OK":
        return 0
    
    count = 0
    for num in mensajes[0].split():
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
                elif "attachment" in dispo:
                    archivo = parte.get_payload(decode=True)
                    archivo_nombre = parte.get_filename()
        else:
            cuerpo == msg.get_payload(decode=True).decode(errors="ignore")

        # Crear boleta sandbox
        sandbox = BoletaSandbox(
            remitente=remitente,
            asunto=asunto,
            mensaje=cuerpo.strip(),
        )

        if archivo:
            sandbox.imagen.save(archivo_nombre, ContentFile(archivo), save=False)

        sandbox.save()
        count += 1


        imap.logout()
        return count