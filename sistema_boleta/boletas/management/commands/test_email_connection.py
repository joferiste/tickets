from django.core.management.base import BaseCommand
from boletas.services.email_ingestor.email_client import (
    verificar_conexion_imap, 
    verificar_conexion_smtp,
    connect_imap,
    connect_smtp
)

class Command(BaseCommand):
    help = 'Prueba las conexiones de email (IMAP y SMTP) de forma segura'

    def add_arguments(self, parser):
        parser.add_argument(
            '--imap',
            action='store_true',
            help='Probar solo conexion IMAP',
        )
        parser.add_argument(
            '--smtp',
            action='store_true',
            help='Probar solo conexion SMTP',
        )

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("🔒 TEST DE CONEXIONES DE EMAIL SEGURAS"))
        self.stdout.write("="*50 + "\n")

        probar_imap = options['imap'] or (not options['imap'] and not options['smtp'])
        probar_smtp = options['smtp'] or (not options['imap'] and not options['smtp'])

        resultados = {
            'imap': None,
            'smtp': None
        }

        # Test IMAP
        if probar_smtp:
            self.stdout.write("\n Probando conexiones IMAP...")
            try:
                with connect_imap(timeout=15) as mail:
                    status, info = mail.select("INBOX", readonly=True)
                    if status == 'OK':
                        # Obtener numero de mensajes
                        status, messages = mail.search(None, 'ALL')
                        num_messages = len(messages[0].split()) if messages[0] else 0

                        self.stdout.write(
                            self.style.SUCCESS(f" IMAP conectado correctamente")                            
                        )
                        self.stdout.write(f" Mensajes en INBOX: {num_messages}")
                        resultados['imap'] = True
                    else:
                        self.stdout.write(
                            self.style.ERROR("Error al seleccionar INBOX")
                        )
                        resultados['imap'] = False
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Error IMAP: {type(e).__name__}")
                )
                self.stdout.write(f"    {str(e)}")
                resultados['imap'] = False

        # Test SMTP
        if probar_smtp:
            self.stdout.write("\n Probando conexión SMTP...")
            try:
                with connect_smtp(timeout=15) as smtp:
                    status = smtp.noop()
                    if status[0] == 250:
                        self.stdout.write(
                            self.style.SUCCESS("  SMTP conectado correctamente")
                        )
                        resultados['smtp'] = True
                    else:
                        self.stdout.write(
                            self.style.ERROR("  Error en verificación SMTP")
                        )
                        resultados['smtp'] = False
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  Error SMTP: {type(e).__name__}")
                )
                self.stdout.write(f"     {str(e)}")
                resultados['smtp'] = False
        
        # Resumen
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.WARNING("RESUMEN"))
        self.stdout.write("="*50)

        if resultados['imap'] is not None:
            status_imap = "OK" if resultados['imap'] else "FAIL"
            self.stdout.write(f"IMAP: {status_imap}")

        if resultados['smtp'] is not None:
            status_smtp = "OK" if resultados['smtp'] else "FAIL"
            self.stdout.write(f"STMP: {status_smtp}")

        # Mensaje final
        self.stdout.write("\n" + "="*50)

        if all(v for v in resultados.values() if v is not None):
            self.stdout.write(
                self.style.SUCCESS("Todas las conexiones funcionan correctamente\n")
            )
        else:
            self.stdout.write(
                self.style.ERROR(" Hay problemas con las conexiones\n")
            )
            self.stdout.write(
                self.style.WARNING(
                    "Verifica:\n"
                    "   1. Credenciales correctas (usar App Password)\n"
                    "   2. Configuracion SSL/TLS\n"
                    "   3. Firewall no bloquea puertos 993/465\n"
                    "   4. Internet funcionando\n"
                )
            )