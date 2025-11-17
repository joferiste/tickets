from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from negocios.forms import NegocioForm, EstadoNegocioForm, CategoriaForm, BusquedaNegocioForm, AsignarLocalForm
from negocios.models import EstadoNegocio, Categoria, Negocio
from locales.models import Local, OcupacionLocal, EstadoLocal   
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic.detail import DetailView
from boletas.models import Boleta, BoletaSandbox
from transacciones.models import Transaccion
from recibos.models import Recibo
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from historiales.models import HistorialNegocio
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from locales.utils import registrar_historial_negocio, detectar_cambios_negocios, registrar_asignacion_local, registrar_desasignacion_local
import re

def CreacionNegocios(request):
    if request.method == 'POST':
        form = NegocioForm(request.POST)
        estado_form = EstadoNegocioForm() 
        categoria_form = CategoriaForm()

        if form.is_valid():
            # Guardar negocio
            nuevo_negocio = form.save()
            registrar_historial_negocio(
                negocio=nuevo_negocio, 
                accion='CREACION',
                tipo_cambio='creacion_negocio',
                descripcion=f"Negocio: '{nuevo_negocio.nombre}' con Descripción: '{nuevo_negocio.descripcion}'",
                estado_nuevo=f"Estado: {nuevo_negocio.estado}, Categoría: {nuevo_negocio.categoria}"
            )
            messages.success(request, '✅ Negocio creado correctamente.')
            return redirect('negocios:create_negocio')
    else:
        form = NegocioForm()
        estado_form = EstadoNegocioForm()
        categoria_form = CategoriaForm()
    return render(request, 'negocios/negocios.html', {'form': form, 'estado_form': estado_form, 'categoria_form': categoria_form})


def crear_estado(request):
    form = NegocioForm()
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "errors": {"general": ["Datos invalidos"]}})       
        estado_form = EstadoNegocioForm(data)
        if estado_form.is_valid():
            nuevo_estado = estado_form.save()
            return JsonResponse({
                'success': True, 
                'id': nuevo_estado.idEstadoNegocio, 
                'nombre': nuevo_estado.nombre})
        else:
            errors = estado_form.errors
            nombre_errors = errors.get('nombre')
            if nombre_errors and nombre_errors[0].startswith("duplicado:"):
                estado_id = nombre_errors[0].split(":")[1]
                estado_existente = EstadoNegocio.objects.get(idEstadoNegocio = estado_id)
                return JsonResponse({
                    "success": False, 
                    "duplicado": True,
                    "id": estado_existente.idEstadoNegocio,
                    "nombre": estado_existente.nombre
                })
        return JsonResponse({'success': False, 'errors': errors})
    estado_form = EstadoNegocioForm()
    return render(request, 'negocios/negocios.html', {'form': form, 'estado_form': estado_form})


def crear_categoria(request):
    form = NegocioForm()
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, "errors": {"general": ["Datos invalidos"]}})
        categoria_form = CategoriaForm(data)
        if categoria_form.is_valid():
            nueva_categoria = categoria_form.save()
            return JsonResponse({
                'success': True, 
                'id': nueva_categoria.idCategoria, 
                'nombre': nueva_categoria.nombre})
        else:
            errors = categoria_form.errors
            nombre_errors = errors.get('nombre')
            if nombre_errors and nombre_errors[0].startswith("duplicado:"):
                categoria_id = nombre_errors[0].split(":")[1]
                categoria_existente = Categoria.objects.get(idCategoria = categoria_id)
                return JsonResponse({
                    "success": False, 
                    "duplicado": True, 
                    "id": categoria_existente.idCategoria, 
                    "nombre": categoria_existente.nombre
                    })
        return JsonResponse({"success": False, "errors": errors})
    categoria_form =  CategoriaForm()   
    return render(request, 'negocios/negocios.html', {'form': form, 'categoria_form': categoria_form})


def visualizar_negocio(request):
    # Obtener todos los negocios
    negocios_lista = Negocio.objects.all().order_by('-fechaCreacion')

    # Manejar búsqueda
    if request.method == "POST":
        form = BusquedaNegocioForm(request.POST)
        if form.is_valid():
            q = form.cleaned_data.get('q', '').strip()
            if q:
                negocios_lista = negocios_lista.filter(nombre__icontains=q)
    else:
        form = BusquedaNegocioForm()

    # Configuración paginación
    paginator = Paginator(negocios_lista, 5)
    page_number = request.GET.get('page', 1)

    try:
        negocios = paginator.page(page_number)
    except PageNotAnInteger:
        negocios = paginator.page(1)
    except EmptyPage:
        negocios = paginator.page(paginator.num_pages)

    context = {
        'form': form,
        'negocios': negocios,
        'total_negocios': paginator.count,
    }

    return render(request, 'negocios/visualizar_negocios.html', context)


def editar_negocio(request, id):
    negocio = get_object_or_404(Negocio, idNegocio=id)
    form = NegocioForm(instance=negocio)

    html = render_to_string("negocios/form_editar_negocio.html", {
        'form': form,
        'negocio': negocio
    }, request=request)

    return JsonResponse({'html': html})


@require_POST
def actualizar_negocio(request):  
    negocio_id = request.POST.get('id')

    if not negocio_id:
        return JsonResponse({
            "success": False, 
            "error": "id del Negocio no proporcionado",
            "message": "Error: ID del negocio no propocionado",
            "message_type": "error",
            })

    negocio = get_object_or_404(Negocio, idNegocio = negocio_id)

    negocio_anterior = Negocio.objects.get(idNegocio=negocio_id)

    form = NegocioForm(request.POST, instance=negocio)

    if form.is_valid():
        negocio_actualizado = form.save()

        # Detectar y guardar cambios en el historial 
        cambios = detectar_cambios_negocios(negocio_anterior, negocio_actualizado)

        # Si no hubo cambios especificos, registrar actualizacion general
        if not cambios:
            registrar_historial_negocio(
                negocio=negocio_actualizado,
                accion='ACTUALIZACION',
                tipo_cambio='actualizacion_general',
                descripcion=f"Negocio '{negocio_actualizado.nombre}' actualizado sin cambios detectados."
            )

            # Construccion del diccionario con los campos que necesitamos actualizar en el DOM
        return JsonResponse({
            "success": True,
            "message": "✅ Negocio actualizado correctamente",
            "message_type": "success", 
            "negocio": {
                "id": negocio.idNegocio, 
                "nombre": negocio.nombre, 
                "descripcion": negocio.descripcion,
                "telefono1": negocio.telefono1, 
                "telefono2": negocio.telefono2 or "---", 
                "email": negocio.email, 
                "nit": negocio.nit or "---",
                "estado": str(negocio.estado), 
                "categoria": str(negocio.categoria)
            }
        })
    else:
        # Retorna el form con errores en HTML para mostrar en el modal
        # Se renderiza nuevamente el formulario con errores
        print(f"Form Errores: {form.errors}") 
        html_form = render_to_string("negocios/form_editar_negocio.html", {
                                    "form": form, 
                                    "negocio": negocio
                                    }, request=request)
        return JsonResponse({
            "success": False, 
            "html": html_form,
            "message":"Error al procesar la actualización",
            "message_type": "error"
            })


@require_POST
def delete_negocio(request):
    negocio_id = request.POST.get('id')
    negocio = get_object_or_404(Negocio, idNegocio=negocio_id)

    # Guardar informacion antes de eliminar
    nombre_negocio = negocio.nombre
    info_local = f"Estado: {negocio.estado}, Categoria: {negocio.categoria}"

    try:
        negocio.delete()

        # Se registra si se elimina correctamente
        registrar_historial_negocio(
            negocio=negocio,
            accion='ELIMINACION',
            tipo_cambio='eliminacion_negocio',
            descripcion=f"Negocio '{nombre_negocio}' eliminado del sistema.",
            estado_anterior=info_local
        )

        return JsonResponse({
            "success":True,
            "negocio_id": negocio_id
        })       
    except ProtectedError:
        return JsonResponse({
            "success": False,
            "error": "❌ No se puede eliminar este negocio porque está asignado a otros elementos."
        })

def negocio_local(request):
    # 1. Obtener ocupaciones activas para mostrar en la tabla
    asignaciones = OcupacionLocal.objects.filter(fecha_fin__isnull=True).select_related('local', 'negocio').order_by('-idOcupacion')

    # 2. Obtener ID's de locales ocupados para filtrar los disponibles
    locales_ocupados_ids = asignaciones.values_list('local_id', flat=True)

    # 3. Excluir esos locales ocupados
    locales_disponibles = Local.objects.exclude(idLocal__in=locales_ocupados_ids) 

    if request.method == 'POST': 
        form = AsignarLocalForm(request.POST)
        form.fields['local'].queryset = locales_disponibles

        if form.is_valid():
            negocio = form.cleaned_data['negocio']
            local = form.cleaned_data['local']
            fecha_inicio = form.cleaned_data['fecha_inicio']

            # Verificar que ese local no esté ya asignado activamente
            if OcupacionLocal.objects.filter(local = local, fecha_fin__isnull=True).exists():
                messages.error(request, f"El local {local.nombre} ya está ocupado.")
            else:
                OcupacionLocal.objects.create(
                    local = local, 
                    negocio = negocio,
                    fecha_inicio = fecha_inicio
                )

                # Cambiar estado del local a Ocupado
                estado_ocupado = get_object_or_404(EstadoLocal, nombre__iexact="Ocupado")
                local.estado = estado_ocupado
                local.save()

                registrar_asignacion_local(
                    local=local,
                    negocio=negocio,
                    fecha_inicio=fecha_inicio
                )

                messages.success(request, f"Local {local.nombre} asignado a {negocio.nombre}.")
                return redirect('negocios:negocio_local')
    else:
        form = AsignarLocalForm()
        form.fields['local'].queryset = locales_disponibles

        # Filtrar los negocios activos
        form.fields['negocio'].queryset = Negocio.objects.filter(estado__nombre='Activo')

    context = {
        'form': form,
        'asignaciones': asignaciones
    }
    return render(request, 'negocios/negocio_local.html', context)


def desasignar_local(request, ocupacion_id):
    ocupacion = get_object_or_404(OcupacionLocal, pk=ocupacion_id, fecha_fin__isnull=True)

    # Guardar referencias antes de modificar
    local = ocupacion.local
    negocio = ocupacion.negocio
    fecha_inicio = ocupacion.fecha_inicio
    fecha_fin = timezone.now().date()

    # Finaliza la Ocupacion
    ocupacion.fecha_fin = fecha_fin
    ocupacion.save()

    # Cambia el estado del local a 'Disponible'
    estado_disponible = get_object_or_404(EstadoLocal, nombre__iexact="Disponible")
    local.estado = estado_disponible
    local.save()

    registrar_desasignacion_local(
        local=local,
        negocio=negocio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    messages.info(request, f"Local {local.nombre} fue desasignado del negocio {ocupacion.negocio.nombre} y marcado como Disponible.")
    return redirect('negocios:negocio_local')


class PerfilNegocioView(DetailView): 
    model = Negocio
    template_name = 'negocios/perfil.html'
    context_object_name = 'negocio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        negocio = self.get_object()
        context['sandbox'] = BoletaSandbox.objects.filter(metadata__negocio_id=negocio.idNegocio).order_by("-fecha_recepcion")
        context['boletas'] = Boleta.objects.filter(negocio=negocio)
        context['transacciones'] = Transaccion.objects.filter(boleta__negocio=negocio)
        context['recibos'] = Recibo.objects.filter(transaccion__boleta__negocio=negocio)
        context['ocupaciones'] = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
        return context
    

def enviar_recibo(request, recibo_id):
    """
    Vista para enviar un recibo por correo electronico
    """
    try:
        recibo = get_object_or_404(Recibo, idRecibo=recibo_id)

        # Verificar que el recibo no haya sido enviado antes
        if recibo.enviado:
            return JsonResponse({
                'status': 'error',
                'message': 'Este recibo ya fue enviado anteriormente.',
            })
        
        # Verificar que el recibo tenga archivo
        if not recibo.archivo:
            return JsonResponse({
                'status': 'error',
                'message': 'El recibo no tiene archivo generado.',
            })
        
        # Preparar el correo
        asunto = f'Recibo oficial - No. {recibo.correlativo}'


        MESES_ES = {
            "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
            "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
            "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
        }
        periodo_str = str(recibo.transaccion.periodo_pagado)
        anio, mes = periodo_str.split('-')
        # Preparar descripcion
        descripcion = f"Mes de {MESES_ES[mes]} del {anio}"



        mensaje_html = f"""
        <html>
        <body>
            <h2>Recibo de Transacción</h2>
            
            <p>Estimado/a <strong>{recibo.transaccion.negocio.usuario.nombre}</strong>,</p>
            
            <p>Adjuntamos el recibo oficial correspondiente a su transacción:</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3>Detalles de la Transacción</h3>
                <p><strong>Negocio:</strong> {recibo.transaccion.negocio.nombre}</p>
                <p><strong>Correlativo:</strong> {recibo.correlativo}</p>
                <p><strong>Período:</strong> {descripcion}</p>
                <p><strong>Monto:</strong> Q.{recibo.transaccion.monto:,.2f}</p>
                <p><strong>Fecha de Transacción:</strong> {recibo.transaccion.fechaTransaccion.strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>UUID de Verificación:</strong> {recibo.uuid}</p>
            </div>
            
            <p>El archivo PDF adjunto constituye su recibo oficial. Consérvelo para sus registros contables.</p>
            
            <p>Si tiene alguna consulta, no dude en contactarnos.</p>
            
            <br>
            <p>Atentamente,<br>
            <strong>Alquileres Comerciales Emanuel</strong></p>
        </body>
        </html>
        """

        email = EmailMessage(
            subject=asunto,
            body=mensaje_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recibo.email],
        )
        email.content_subtype = 'html'

        # Adjuntar el PDF
        with recibo.archivo.open('rb') as archivo:
            email.attach(f'{recibo.nombre}.pdf', archivo.read(), 'application/pdf')

        # Enviar el correo
        email.send()

        # Actualizar el estado del recibo
        with transaction.atomic():
            recibo.enviado = True
            recibo.fechaEnvio = timezone.now()
            recibo.mensajeEnvio = f"Enviado correctamente a {recibo.email} "
            recibo.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Recibo enviado correctamente por correo electronico.'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al enviar el recibo: {str(e)}'
        })
    
@require_http_methods(["POST"])
@csrf_exempt
def reenviar_recibo(request, recibo_id):
    """
    Vista para reenviar un recibo que ya fue enviado anteriormente
    """

    try:
        recibo = get_object_or_404(Recibo, idRecibo=recibo_id)

        # Verificar que el recibo haya sido enviado anteriormente
        if not recibo.enviado:
            return JsonResponse({
                'status': 'error',
                'message': 'Este recibo no ha sido enviado antes, use la opcion -Enviar- en su lugar.'
            })
        
        # Verificar que el recibo tenga archivo
        if not recibo.archivo:
            return JsonResponse({
                'status': 'error',
                'message': 'El recibo no tiene archivo generado.'
            })
        
        # Preparar el correo de reenvio
        asunto = f'REENVIO -  Recibo Oficial - No. {recibo.correlativo}'

        mensaje_html = f"""
<html>
        <body>
            <h2>Reenvío de Recibo de Transacción</h2>
            
            <p>Estimado/a <strong>{recibo.transaccion.negocio.usuario.name}</strong>,</p>
            
            <p>Le reenviamos el recibo oficial correspondiente a su transacción:</p>
            
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                <p><strong>NOTA:</strong> Este es un reenvío del recibo original enviado el {recibo.fechaEnvio.strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>Detalles de la Transacción</h3>
                <p><strong>Negocio:</strong> {recibo.transaccion.negocio.nombre}</p>
                <p><strong>Correlativo:</strong> {recibo.correlativo}</p>
                <p><strong>Período:</strong> {recibo.transaccion.periodo_pagado}</p>
                <p><strong>Monto:</strong> Q.{recibo.transaccion.monto:,.2f}</p>
                <p><strong>Fecha de Transacción:</strong> {recibo.transaccion.fechaTransaccion.strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>UUID de Verificación:</strong> {recibo.uuid}</p>
            </div>
            
            <p>El archivo PDF adjunto constituye su recibo oficial. Consérvelo para sus registros contables.</p>
            
            <br>
            <p>Atentamente,<br>
            <strong>Sistema de Alquileres Comerciales</strong></p>
        </body>
        </html>
        """ 

        # Crear y enviar el email
        email = EmailMessage(
            subject=asunto,
            body=mensaje_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recibo.email],
        )
        email.content_subtype = 'html'

        # Adjuntar el PDF
        with recibo.archivo.open('rb') as archivo:
            email.attach(f'{recibo.nombre}.pdf', archivo.read(), 'application/pdf')

        # Enviar el correo
        email.send()

        # Actualizar el mensaje de envio con informacion de reenvio
        with transaction.atomic:
            mensaje_anterior = recibo.mensajeEnvio or ""
            recibo.mensajeEnvio = f"{mensaje_anterior}\nReenviado el {timezone.now().strftime('%d/%m/%Y %H:%M')}"

        return JsonResponse({
            'status': 'success',
            'message': 'Recibo reenviado correctamente por correo electronico.'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error al reenviar el recibo: {str(e)}'
        })
    
def recibo_detalles(request, recibo_id):
    """
    Vista para agregar detalles completo del recibo
    """

    try:
        recibo = get_object_or_404(Recibo, idRecibo=recibo_id)

        context = {
            'recibo': recibo,
            'transaccion': recibo.transaccion,
            'negocio': recibo.transaccion.negocio,
            'usuario': recibo.transaccion.negocio.usuario,
        }

        return render(request, 'negocios/recibo_detalles.html', context)
    
    except Exception as e:
        context = {
            'error': f'Error al cargar detalles del recibo: {str(e)}'
        }
    return render(request, 'negocios/error.html', context)


def mantenimiento_negocios(request):
    """ Vista principal del mantenimiento de negocios -edicion- """

    if request.method == 'POST':
        # Determinar si es peticion AJAX
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        tipo = request.POST.get('tipo')
        item_id = request.POST.get('item_id')
        nombre = request.POST.get('nombre', '').strip()

        if not nombre:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'El nombre es requerido'}, status=400)
            messages.error(request, 'El nombre es requerido')
            return redirect('negocios:mantenimiento_negocios')
        
        if re.search(r'\d', nombre):
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'El nombre no puede contener números'}, status=400)
            messages.error(request, 'El nombre no puede contener números')
            return redirect('negocios:mantenimiento_negocios')

        try:
            if tipo == 'estado':
                estado = get_object_or_404(EstadoNegocio, idEstadoNegocio=item_id)
                estado.nombre = nombre
                estado.save()
                mensaje = f"Estado '{nombre}' ha sido actualizado exitosamente"
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': mensaje,
                        'data': {
                            'id': estado.idEstadoNegocio,
                            'nombre': estado.nombre
                        }
                    })
                messages.success(request, mensaje)

            elif tipo == 'categoria':
                categoria = get_object_or_404(Categoria, idCategoria=item_id)
                categoria.nombre = nombre
                categoria.save()
                mensaje = f"Categoría '{nombre}' ha sido actualizado correctamente"

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': mensaje,
                        'data': {
                            'id': categoria.idCategoria,
                            'nombre': categoria.nombre
                        }
                    })
                messages.success(request, mensaje)

        except Exception as e:
            error_msg = f'Error al actualizar: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg}, status=500)
            messages.error(request, error_msg)

        return redirect('negocios:mantenimiento_negocios')
    
    # Mostrar los elementos 
    estados = EstadoNegocio.objects.all().order_by('idEstadoNegocio')
    categorias = Categoria.objects.all().order_by('idCategoria')

    return render(request, 'negocios/mantenimiento_negocios.html', {
        'estados': estados,
        'categorias': categorias
    })

@require_http_methods(["POST"])
def eliminar_elemento_negocio(request):
    item_id = request.POST.get('item_id')
    tipo = request.POST.get('tipo')

    try:
        if tipo == 'estado':
            estado = get_object_or_404(EstadoNegocio, idEstadoNegocio=item_id)
            nombre = estado.nombre
            estado.delete()
            messages.success(request, f"Estado '{nombre}' fue eliminado correctamente")
        elif tipo == 'categoria':
            categoria = get_object_or_404(Categoria, idCategoria=item_id)
            nombre = categoria.nombre
            categoria.delete()
            messages.success(request, f"Categoria '{nombre}' fue eliminado correctamente")
    except Exception as e:
        messages.error(request, f'Error al eliminar el elemento: {str(e)}')
    return redirect('negocios:mantenimiento_negocios')