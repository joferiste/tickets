from django.db.models.signals import post_save
from django.dispatch import receiver
from recibos.models import Recibo
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.files.base import ContentFile
import re
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
import datetime
import traceback
from administracion.views import slugify_filename
from recibos.utils.recibo_helper import (
    analizar_transaccion_recibo,
    generar_tabla_detalle_transaccion,
    generar_seccion_excedente_html,
    generar_observaciones_especiales,
    _get_descripcion_estado_excedente,
    obtener_tipo_recibo,
)

@receiver(post_save, sender=Recibo)
def generar_pdf_recibo(sender, instance, created, **kwargs):
    """
    Signal que genera automáticamente el PDF cuando se crea un recibo
    se agrega logica para manejar excedentes y estados especiales.
    """
    # Solo ejecutar cuando se crea y no tiene archivo
    print(f"Signal ejecutado - created: {created}, tiene archivo: {bool(instance.archivo)}")
    if created and not instance.archivo:
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer, 
                pagesize=letter, 
                topMargin=0.5*inch,
                bottomMargin=0.5*inch,
                leftMargin=0.5*inch,
                rightMargin=0.5*inch
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # NUEVO: Analizar la transacción usando el helper
            info_transaccion = analizar_transaccion_recibo(instance.transaccion)
            tipo_recibo = obtener_tipo_recibo(instance.transaccion)
            
            # Estilo personalizado para encabezados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1,  # Centrado
                textColor=colors.black
            )
            
            # === ENCABEZADO DE LA EMPRESA ===
            empresa_data = [
                ['ALQUILERES COMERCIALES EMANUEL', ''],
                ['Fabiana Vicente de Riscajché', ''],
                ['Calle del Rastro zona 4, Retalhuleu', ''],
                ['NIT: 12345678-9', ''],
                [f'Fecha de Emisión: {instance.fechaGeneracion.strftime("%d/%m/%Y")}', f'No. Recibo: {instance.correlativo}'],
                ['', f'Verificación UUID: {str(instance.uuid)}']
            ]
            
            empresa_table = Table(empresa_data, colWidths=[4*inch, 3*inch])
            empresa_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, 3), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTSIZE', (0, 0), (0, 0), 14),
                ('ALIGN', (1, 4), (1, 4), 'RIGHT'),  # Número de recibo a la derecha
                ('ALIGN', (1, 5), (1, 5), 'RIGHT'),
                ('FONTNAME', (1, 5), (1, 5), 'Helvetica-Oblique'),  # 👈 cursiva
                ('FONTSIZE', (1, 5), (1, 5), 9),  # 👈 más pequeño
                ('TEXTCOLOR', (1, 5), (1, 5), colors.grey),  # 👈 gris tenue tipo "sello digital"
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(empresa_table)
            story.append(Spacer(1, 0.1*inch))
            
            # === TÍTULO DEL RECIBO (MODIFICADO SEGÚN EL TIPO) ===
            if tipo_recibo == 'con_excedente':
                titulo_texto = "RECIBO OFICIAL - CON EXCEDENTE"
            elif tipo_recibo == 'con_mora':
                titulo_texto = "RECIBO OFICIAL - CON RECARGO"
            else:
                titulo_texto = "RECIBO OFICIAL"
                
            titulo = Paragraph(titulo_texto, title_style)
            story.append(titulo)
            
            # === DATOS DEL CLIENTE ===
            cliente_data = [
                ['DATOS DEL CLIENTE', ''],
                ['Nombre:', instance.transaccion.negocio.usuario.nombre],
                ['Negocio:', instance.transaccion.negocio.nombre],
                ['Correo:', instance.email],
            ]
            
            cliente_table = Table(cliente_data, colWidths=[2*inch, 5*inch])
            cliente_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            
            story.append(cliente_table)
            story.append(Spacer(1, 0.2*inch))
            
            # === DETALLE DE LA TRANSACCIÓN (USANDO EL HELPER) ===
            detalle_data = generar_tabla_detalle_transaccion(instance.transaccion, info_transaccion)
            
            detalle_table = Table(detalle_data, colWidths=[0.8*inch, 3.7*inch, 1.5*inch, 1.5*inch])
            detalle_table.setStyle(TableStyle([
                # Encabezados
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                
                # Contenido
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.black),
                
                # Totales (últimas 3 filas)
                ('FONTNAME', (2, -2), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                
                # Espaciado
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                
                # Total final destacado
                ('BACKGROUND', (3, -1), (-1, -1), colors.lightgrey),
                ('FONTSIZE', (2, -1), (-1, -1), 12),
            ]))
            
            story.append(detalle_table)
            story.append(Spacer(1, 0.4*inch))
            
            # === SECCIÓN ESPECIAL PARA EXCEDENTES ===
            if info_transaccion['tiene_excedente']:
                excedente_info = info_transaccion['seccion_excedente']
                
                # Crear tabla especial para excedente
                excedente_data = [
                    ['INFORMACIÓN DEL EXCEDENTE', ''],
                    ['Monto del excedente:', f'Q.{excedente_info["monto"]:,.2f}'],
                    ['Estado del excedente:', excedente_info['descripcion_estado']],
                ]
                
                if info_transaccion['estado_especial'] == 'espera_acreditacion':
                    excedente_data.append(['Acción requerida:', 'Pendiente de acreditación para uso futuro'])
                elif info_transaccion['estado_especial'] == 'excedente_disponible':
                    excedente_data.append(['Disponibilidad:', 'Listo para aplicar en próximos pagos'])
                
                excedente_table = Table(excedente_data, colWidths=[2.5*inch, 4.5*inch])
                excedente_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                
                story.append(excedente_table)
                story.append(Spacer(1, 0.2*inch))
            
            # === OBSERVACIONES (USANDO EL HELPER) ===
            observaciones = generar_observaciones_especiales(info_transaccion)
            
            if observaciones or instance.transaccion.comentario:
                obs_text = "<b>OBSERVACIONES:</b><br/>"
                
                # Agregar observaciones del helper
                for obs in observaciones:
                    obs_text += f"• {obs}<br/>"
                
                # Agregar comentarios de la transacción si existen
                if instance.transaccion.comentario:
                    obs_text += f"<br/><b>Detalles técnicos:</b><br/>{instance.transaccion.comentario}"
                
                story.append(Paragraph(obs_text, styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            

            
            # === PIE DE PÁGINA ===
            pie_texto = """
            <i>Este recibo ha sido generado electrónicamente y tiene validez oficial.<br/>
            Para verificar su autenticidad, use el UUID proporcionado en nuestro sistema.<br/>
            Documento generado automáticamente - No requiere sello ni firma manuscrita.</i>
            """
            story.append(Paragraph(pie_texto, styles['Normal']))
            
            # Construir el PDF
            doc.build(story)
            buffer.seek(0)
            
            # Generar nombre del archivo usando la función auxiliar
            
            negocio_limpio = slugify_filename(instance.transaccion.negocio.nombre)
            fecha_archivo = instance.fechaGeneracion.strftime('%Y%m%d')
            file_name = f"{instance.correlativo}-{fecha_archivo}-{negocio_limpio}-{str(instance.uuid)[:8]}.pdf"
            
            # Guardar el archivo SIN llamar a save() para evitar recursión
            instance.archivo.save(
                file_name, 
                ContentFile(buffer.read()),
                save=False
            )
            buffer.close()
            
            # Actualizar el campo archivo directamente en la DB
            Recibo.objects.filter(pk=instance.pk).update(archivo=instance.archivo)
            
            print(f"PDF generado exitosamente con lógica de excedentes: {file_name}")
            
        except Exception as e:
            print(f"Error generando PDF para recibo {instance.idRecibo}: {str(e)}")
            traceback.print_exc()