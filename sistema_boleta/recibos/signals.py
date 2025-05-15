from django.db.models.signals import post_save
from django.dispatch import receiver
from recibos.models import Recibo
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.files.base import ContentFile


@receiver(post_save, sender=Recibo)
def generar_pdf_recibo(sender, instance, created, **kwargs):
    if created and not instance.archivo:
        buffer = BytesIO() 
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Contenido del recibo
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Recibo De Transaccion Completada")

        c.setFont("Helvetica", 12)
        c.drawString(50, height - 100, f"Negocio: {instance.transaccion.negocio.nombre}")
        c.drawString(50, height - 120, f"Correo: {instance.transaccion.boleta.email}")
        c.drawString(50, height - 140, f"Numero de Boleta: {instance.transaccion.boleta.numeroBoleta}")
        c.drawString(50, height - 160, f"Monto: {instance.transaccion.boleta.monto}")
        c.drawString(50, height - 180, f"Fecha de Transaccion: {instance.transaccion.fechaTransaccion.strftime('%Y-%m-%d %H:%M')}")
        c.drawString(50, height - 200, f"UUID: {instance.uuid}")
        c.drawString(50, height - 240, "Firma electronica automatica.")

        c.showPage()
        c.save()

        buffer.seek(0)
        file_name = f"recibo_{instance.transaccion_negocio.nombre}_{instance.uuid}.pdf"
        instance.archivo.save(file_name, ContentFile(buffer.read()))
        buffer.close()
        instance.save()