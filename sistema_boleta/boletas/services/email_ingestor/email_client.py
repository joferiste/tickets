import imaplib
from django.conf import settings

def connect_imap():
    try:
        if settings.EMAIL_USE_SSL:
            mail = imaplib.IMAP4_SSL(settings.EMAIL_SERVER, settings.EMAIL_PORT)
        else:
            mail = imaplib.IMAP4(settings.EMAIL_SERVER, settings.EMAIL_PORT)

        mail.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        return mail
    except Exception as e:
        print(f"[ERROR] No se puede conectar al servidor de correo: {e}")
        return None
