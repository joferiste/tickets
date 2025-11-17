from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from locales.forms import LocalForm, EstadoLocalForm, NivelForm, UbicacionForm, BusquedaLocalForm, AsignarPosicionMapaForm
from locales.models import Nivel, EstadoLocal, Ubicacion, Local
from transacciones.models import Transaccion
import json
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.db.models.deletion import ProtectedError
from historiales.models import HistorialLocal
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal, InvalidOperation
from django.db.models import Sum, Count, Q
from django.utils import timezone
import re
from .utils import registrar_historial_local, detectar_cambios_local
from django.views.decorators.http import require_http_methods

def crear_local(request):
    max_locales = 8
    total_locales = Local.objects.count()
    bloqueado = total_locales >= max_locales
    
    if request.method == 'POST':
        if bloqueado:
            messages.warning(request, '⚠️ Ya se alcanzó el número máximo de locales permitidos (8). Elimine uno para crear otro.')
            return redirect('locales:create_local')
        
        form = LocalForm(request.POST)
        estado_form = EstadoLocalForm()
        nivel_form = NivelForm()
        ubicacion_form = UbicacionForm()

        if form.is_valid():
            # Guardar local
            nuevo_local = form.save()

            # Registrar en el historial
            registrar_historial_local(
                local=nuevo_local, 
                accion='CREACION',
                tipo_cambio='creacion_local',
                descripcion=f"Local '{nuevo_local.nombre}' creado con costo de Q.{nuevo_local.nivel.costo}.",
                estado_nuevo=f"Estado: {nuevo_local.estado}, Nivel: {nuevo_local.nivel}."
            )
            
            messages.success(request, '✅ Local creado correctamente.')
            return redirect('locales:create_local')
    else:
        form = LocalForm()
        estado_form = EstadoLocalForm()
        nivel_form = NivelForm()
        ubicacion_form = UbicacionForm()
    return render(request, 'locales/locales.html', {'form': form, 'estado_form': estado_form, 'nivel_form': nivel_form, 'ubicacion_form': ubicacion_form, 'bloqueado': bloqueado})


def crear_estado(request):
    form = LocalForm()
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "errors": {"general": ["Datos invalidos"]}})       
        estado_form = EstadoLocalForm(data)
        if estado_form.is_valid():
            nuevo_estado = estado_form.save()
            return JsonResponse({
                'success': True, 
                'id': nuevo_estado.idEstado, 
                'nombre': nuevo_estado.nombre})
        else:
            errors = estado_form.errors
            nombre_errors = errors.get('nombre')
            if nombre_errors and nombre_errors[0].startswith("duplicado:"):
                estado_id = nombre_errors[0].split(":")[1]
                estado_existente = EstadoLocal.objects.get(idEstado = estado_id)
                return JsonResponse({
                    "success": False, 
                    "duplicado": True,
                    "id": estado_existente.idEstado,
                    "nombre": estado_existente.nombre
                })
        return JsonResponse({'success': False, 'errors': errors})
    estado_form = EstadoLocalForm()
    return render(request, 'locales/locales.html', {'form': form, 'estado_form': estado_form})


def crear_nivel(request):
    form = LocalForm()
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, "errors": {"general": ["Datos invalidos"]}})
        nivel_form = NivelForm(data)
        if nivel_form.is_valid():
            nuevo_nivel = nivel_form.save()
            return JsonResponse({
                'success': True, 
                'id': nuevo_nivel.idNivel, 
                'nombre': nuevo_nivel.nombre})
        else:
            errors = nivel_form.errors
            nombre_errors = errors.get('nombre')
            if nombre_errors and nombre_errors[0].startswith("duplicado:"):
                nivel_id = nombre_errors[0].split(":")[1]
                nivel_existente = Nivel.objects.get(idNivel = nivel_id)
                return JsonResponse({
                    "success": False, 
                    "duplicado": True, 
                    "id": nivel_existente.idNivel, 
                    "nombre": nivel_existente.nombre
                    })
        return JsonResponse({"success": False, "errors": errors})
    nivel_form =  NivelForm()   
    return render(request, 'locales/locales.html', {'form': form, 'nivel_form': nivel_form})


def crear_ubicacion(request):
    form = UbicacionForm()
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, "errors": {"general": ["Datos invalidos"]}})
        ubicacion_form = UbicacionForm(data)
        if ubicacion_form.is_valid():
            nueva_ubicacion = ubicacion_form.save()
            return JsonResponse({
                'success': True, 
                'id': nueva_ubicacion.idUbicacion, 
                'nombre': nueva_ubicacion.nombre})
        else:
            errors = ubicacion_form.errors
            nombre_errors = errors.get('nombre')
            if nombre_errors and nombre_errors[0].startswith("duplicado:"):
                ubicacion_id = nombre_errors[0].split(":")[1]
                ubicacion_existente = Ubicacion.objects.get(idUbicacion = ubicacion_id)
                return JsonResponse({
                    "success": False, 
                    "duplicado": True, 
                    "id": ubicacion_existente.idUbicacion, 
                    "nombre": ubicacion_existente.nombre
                    })
        return JsonResponse({"success": False, "errors": errors})
    ubicacion_form =  UbicacionForm()   
    return render(request, 'locales/locales.html', {'form': form, 'ubicacion_form': ubicacion_form})


def visualizar_local(request):

    locales_lista = Local.objects.all().order_by('-fechaCreacion')

    # Manejar busqueda
    if request.method == "POST":
        form = BusquedaLocalForm(request.POST)
        if form.is_valid():
            q = form.cleaned_data.get('q', '').strip()
            if q:
                locales_lista = locales_lista.filter(nombre__icontains=q)
    else:
        form = BusquedaLocalForm()

    # Configurar paginacion
    paginator = Paginator(locales_lista, 5)
    page_number = request.GET.get('page', 1)

    try:
        locales = paginator.page(page_number)
    except PageNotAnInteger:
        locales = paginator.page(1)
    except EmptyPage:
        locales = paginator.page(paginator.num_pages)

    context = {
        'form': form,
        'locales': locales,
        'total_locales': paginator.count,
    }

    return render(request, 'locales/visualizar_locales.html', context)



def editar_local(request, id):
    local = get_object_or_404(Local, idLocal=id)

    # Se indica que es una edicion
    form = LocalForm(instance=local, es_edicion=True)

    html = render_to_string("locales/form_editar_locales.html", {
        'form': form,
        'local': local
    }, request=request)
    
    return JsonResponse({'html':html}) 


@require_POST
def actualizar_local(request):
    local_id = request.POST.get('id')
    
    if not local_id:
        return JsonResponse({
            "success": False, 
            "error": "ID de local no proporcionado",
            "message": "Error: ID del local no encontrado",
            "message_type":"error"
        })
    
    local = get_object_or_404(Local, idLocal=local_id)

    # Guardar estado anterior para comparacion
    local_anterior = Local.objects.get(idLocal=local_id)

    #Nuevamente, es una edicion
    form = LocalForm(request.POST, instance=local, es_edicion=True)

    if form.is_valid():
        local_actualizado = form.save()

        # Detectar y registrar cambios en el historial
        cambios = detectar_cambios_local(local_anterior, local_actualizado)

        # Si no hubo cambios especificos, registrar actualizacion general
        if not cambios:
            registrar_historial_local(
                local=local_actualizado,
                accion='ACTUALIZACION',
                tipo_cambio='actualizacion_general',
                descripcion=f"Local '{local_actualizado.nombre}' actualizado sin cambios detectados."
            )

        return JsonResponse({
            "success": True,
            "message": "✅ Local actualizado correctamente",
            "message_type": "success",
            "local": {
                "id": local.idLocal,
                "nombre": local.nombre,
                "estado": str(local.estado),
                "nivel": str(local.nivel)
            }
        })
    else:
        print(f"Form errores: {form.errors}")
        html = render_to_string("locales/form_editar_locales.html", {
            "form": form,
            "local": local
        }, request=request)
        return JsonResponse({
            "success": False,
            "html": html,
            "message":"Error al procesar la actualización",
            "message_type": "error"
        })


@require_POST
def delete_local(request):
    local_id = request.POST.get('id')
    local = get_object_or_404(Local, idLocal=local_id)

    # Guardar informacion antes de eliminar
    nombre_local = local.nombre
    info_local = f"Estado: {local.estado}, Nivel: {local.nivel}, Costo: Q.{local.costo}"

    try:
        registrar_historial_local(
            local=local,
            accion='ELIMINACION',
            tipo_cambio='eliminacion_local',
            descripcion=f"Local '{nombre_local}' ha sido eliminado del sistema.",
            estado_anterior=info_local
        )

        local.delete()

        return JsonResponse({
            "success":True,
            "local_id": local_id
        })       
    except ProtectedError:
        return JsonResponse({
            "success": False,
            "error": "❌ No se puede eliminar este usuario porque está asignado a otros elementos."
        })

def orden_local(request):
    locales = Local.objects.all().order_by('idLocal')
    posiciones_ocupadas = Local.objects.exclude(posicionMapa__isnull=True).values_list('posicionMapa', flat=True)

    if request.method == 'POST':
        if 'asignar_posicion' in request.POST:
            form = AsignarPosicionMapaForm(request.POST, posiciones_ocupadas=posiciones_ocupadas)
            if form.is_valid():
                local = form.cleaned_data['local']
                posicion = int(form.cleaned_data['posicionMapa'])

                # Guardar posicion anterior
                posicion_anterior = local.posicionMapa

                local.posicionMapa = posicion
                local.save()

                # Registrar el historial
                registrar_historial_local(
                    local=local,
                    accion='ACTUALIZACION',
                    tipo_cambio='posicion_mapa',
                    descripcion=f"Se asigno a la posición {posicion} en el mapa.",
                    estado_anterior=str(posicion_anterior) if posicion_anterior else "Sin posición",
                    estado_nuevo=str(posicion)
                )

                messages.success(request, f"Se asignó la posición {posicion} al local {local.nombre}.")
                return redirect('locales:orden_local')
            
        elif 'desasignar_posicion' in request.POST:
            local_id = request.POST.get('local_id')
            local = get_object_or_404(Local, pk=local_id)

            # Validacion: Verificar si el local esta ocupado
            if local.estado and local.estado.nombre == 'Ocupado':
                messages.error(request, f"No se puede desasignar la posicion del local: '{local.nombre}' porque tiene un negocio asignado.")
                return redirect('locales:orden_local')
            
            posicion = local.posicionMapa
            local.posicionMapa = None
            local.save()

            # Registrar en el historial
            registrar_historial_local(
                local=local,
                accion='ACTUALIZACION',
                tipo_cambio='posicion_mapa',
                descripcion=f"Se desasignó la posición {posicion} del mapa.",
                estado_anterior=str(posicion),
                estado_nuevo= "Sin posición"
            )
            messages.info(request, f"Se desasignó la posición {posicion} del local {local.nombre}.")
            return redirect('locales:orden_local')
        
        elif 'reiniciar' in request.POST:
            # Validacion: Verificar si hay locales ocupados
            locales_ocupados = Local.objects.filter(
                estado__nombre='Ocupado',
                posicionMapa__isnull=False
            )

            if locales_ocupados.exists():
                nombres_ocupados = ', '.join([local.nombre for local in locales_ocupados])
                messages.error(request, f"No se puede reiniciar porque los siguientes locales tienen negocios asignados {nombres_ocupados}.")
                return redirect('locales:orden_local')
            
            # Registrar en historial antes de reiniciar
            locales_con_posicion = Local.objects.exclude(posicionMapa__isnull=True)
            for local in locales_con_posicion:
                registrar_historial_local(
                    local=local,
                    accion='ACTUALIZACION',
                    tipo_cambio='posicion_mapa',
                    descripcion=f"Posición {local.posicionMapa} desasignado por reinicio general.",
                    estado_anterior=str(local.posicionMapa),
                    estado_nuevo="Sin posición"
                )

            Local.objects.update(posicionMapa=None)
            messages.warning(request, "Se han desasignado todas las posiciones.")
            return redirect('locales:orden_local')

    context = {
        'locales': locales,
        'posiciones_ocupadas': list(posiciones_ocupadas)
    }
    return render(request, 'locales/orden_local.html', context)

    
def desasignar_posicion(request, local_id):
    local = get_object_or_404(Local, idLocal=local_id)

    # Validacion: verificacion si el local esta ocupado
    if local.estado and local.estado.nombre == 'Ocupado':
        messages.error(request, f"No se puede desasignar la posición del local '{local.nombre}' porque tiene un negocio asignado.")
        return redirect('locales:orden_local')
    
    # Si el local no tiene posicion asignada
    if local.posicionMapa is None:
        messages.warning(request, f"El local '{local.nombre}' no tiene posición en el mapa asignada.")
        return redirect('locales:orden_local')
    
    posicion_anterior = local.posicionMapa
    local.posicionMapa = None
    local.save()

    # Registrar en historial
    registrar_historial_local(
        local=local,
        accion='ACTUALIZACION',
        tipo_cambio='posicion_mapa',
        descripcion=f"Se desasignó la posición {posicion_anterior} del mapa.",
        estado_anterior=str(posicion_anterior),
        estado_nuevo= "Sin posición"
    )
    
    messages.success(request, f"La posición del local {local.nombre} ha sido desasignada.")
    return redirect('locales:orden_local')


@login_required
def perfil_local(request, local_id):
    """Vista para mostrar el perfil completo de un local"""
    local = get_object_or_404(Local, idLocal=local_id)
    
    # Ocupación actual
    ocupacion_actual = local.ocupaciones.filter(fecha_fin__isnull=True).first()
    
    # Ocupaciones pasadas (todas, incluyendo la actual)
    ocupaciones_pasadas = local.ocupaciones.all().order_by('-fecha_inicio')
    
    # Últimos movimientos del historial
    ultimos_movimientos = HistorialLocal.objects.filter(
        local=local
    ).order_by('-fechaModificacion')[:5]
    
    # ========================================
    # CÁLCULO CORRECTO DE INGRESOS TOTALES
    # ========================================
    ingresos_totales = Decimal('0.00')
    total_transacciones = 0
    detalle_ingresos = []  # Para debugging/mostrar detalle si quieres

    # Recorrer todas las ocupaciones de este local
    for ocupacion in ocupaciones_pasadas:
        fecha_inicio = ocupacion.fecha_inicio
        fecha_fin = ocupacion.fecha_fin or timezone.now().date()
        
        # Generar lista de periodos válidos (YYYY-MM)
        periodos_validos = []
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            periodos_validos.append(fecha_actual.strftime('%Y-%m'))
            # Avanzar al siguiente mes
            if fecha_actual.month == 12:
                fecha_actual = fecha_actual.replace(year=fecha_actual.year + 1, month=1)
            else:
                fecha_actual = fecha_actual.replace(month=fecha_actual.month + 1)
        
        # Obtener transacciones exitosas del negocio en ese periodo
        transacciones_periodo = Transaccion.objects.filter(
            negocio=ocupacion.negocio,
            estado='exitosa',
            periodo_pagado__in=periodos_validos
        )
        
        # CORRECCIÓN: Sumar el MONTO REAL de cada transacción
        # (esto incluye mora, ajustes, etc.)
        resultado = transacciones_periodo.aggregate(
            total=Sum('monto'),
            cantidad=Count('idTransaccion')
        )
        
        monto_ocupacion = resultado['total'] or Decimal('0.00')
        cantidad_transacciones = resultado['cantidad'] or 0
        
        ingresos_totales += monto_ocupacion
        total_transacciones += cantidad_transacciones
        
        # Opcional: Guardar detalle para debugging
        if monto_ocupacion > 0:
            detalle_ingresos.append({
                'negocio': ocupacion.negocio.nombre,
                'periodo': f"{fecha_inicio} - {fecha_fin or 'Actual'}",
                'monto': monto_ocupacion,
                'transacciones': cantidad_transacciones
            })

    context = {
        'local': local,
        'ocupacion_actual': ocupacion_actual,
        'ocupaciones_pasadas': ocupaciones_pasadas,
        'ultimos_movimientos': ultimos_movimientos,
        'ingresos_totales': f"{ingresos_totales:.2f}", 
        'total_transacciones': total_transacciones,
        'detalle_ingresos': detalle_ingresos,  
    }
    
    return render(request, 'locales/profile.html', context)


def mantenimiento_locales(request):
    """ Vista principal del mantenimiento de locales -edicion- """

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
            return redirect('locales:mantenimiento_locales')
        
        if re.search(r'\d', nombre):
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'El nombre no puede contener números'}, status=400)
            messages.error(request, 'El nombre no puede contener números')
            return redirect('locales:mantenimiento_locales')

        try:
            if tipo == 'estado':
                estado = get_object_or_404(EstadoLocal, idEstado=item_id)
                estado.nombre = nombre
                estado.save()
                mensaje = f"Estado '{nombre}' ha sido actualizado exitosamente"
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': mensaje,
                        'data': {
                            'id': estado.idEstado,
                            'nombre': estado.nombre
                        }
                    })
                messages.success(request, mensaje)

            elif tipo == 'nivel':
                # Obtener nivel existente
                nivel = get_object_or_404(Nivel, idNivel=item_id)

                # Actualizar nombre (siempre viene)
                nivel.nombre = nombre

                # Actualizar costo si viene en el POST
                costo_str = request.POST.get('costo', '').strip()
                if costo_str:
                    try:
                        costo = Decimal(costo_str)
                        if costo <= 0:
                            raise ValueError("El costo debe ser mayor a 0")
                        nivel.costo = costo
                    except (InvalidOperation, ValueError) as e: 
                        error = f'Costo inválido: {str(e)}'
                        if is_ajax:
                            return JsonResponse({'success': False, 'error': error}, status=400)
                        messages.error(request, error)
                        return redirect('locales:mantenimiento_locales')

            
                # Actualizar ubicacion si viene en el POST
                ubicacion_id = request.POST.get('ubicacion', '').strip()
                if ubicacion_id:
                    try:
                        ubicacion = get_object_or_404(Ubicacion, idUbicacion=ubicacion_id)
                        nivel.ubicacion = ubicacion
                    except Exception as e:
                        error = f'Ubicación inválida: {str(e)}'
                        if is_ajax:
                            return JsonResponse({'success': False, 'error': error}, status=400)
                        messages.error(request, error)
                        return redirect('locales:mantenimiento_locales')

                # Guardar cambios
                nivel.save()
                mensaje = f"Nivel '{nombre}' ha sido actualizado correctamente"

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': mensaje,
                        'data': {
                            'id': nivel.idNivel,
                            'nombre': nivel.nombre,
                            'costo': str(nivel.costo),
                            'ubicacion': nivel.ubicacion.nombre,
                            'ubicacion_id': nivel.ubicacion.idUbicacion
                        }
                    })
                messages.success(request, mensaje)

            elif tipo == 'ubicacion':
                ubicacion = get_object_or_404(Ubicacion, idUbicacion=item_id)
                ubicacion.nombre = nombre
                ubicacion.save()
                mensaje = f"Ubicación '{nombre}' ha sido actualizado correctamente"

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': mensaje,
                        'data': {
                            'id': ubicacion.idUbicacion,
                            'nombre': ubicacion.nombre
                        }
                    })
                messages.success(request, mensaje)

        except Exception as e:
            error_msg = f'Error al actualizar: {str(e)}'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg}, status=500)
            messages.error(request, error_msg)

        return redirect('locales:mantenimiento_locales')
    
    # GET: Mostrar los elementos
    estados = EstadoLocal.objects.all().order_by('idEstado')
    niveles = Nivel.objects.select_related('ubicacion').all().order_by('idNivel')
    ubicaciones = Ubicacion.objects.all().order_by('idUbicacion')

    return render(request, 'locales/mantenimiento_locales.html', {'estados': estados, 'niveles': niveles, 'ubicaciones': ubicaciones})


@require_http_methods(["POST"])
def eliminar_elemento_local(request):
    """ Eliminar estado, nivel o ubicacion"""
    item_id = request.POST.get('item_id')
    tipo = request.POST.get('tipo')
    tab_actual = request.GET.get('tab', 'estados')
    try:
        if tipo == 'estado':
            estado = get_object_or_404(EstadoLocal, idEstado=item_id)
            nombre = estado.nombre
            estado.delete()
            messages.success(request, f"Estado '{nombre}' fue eliminado correctamente")

        elif tipo == 'nivel':
            nivel = get_object_or_404(Nivel, idNivel=item_id)
            nombre = nivel.nombre
            nivel.delete()
            messages.success(request, f"Nivel '{nombre}' fue eliminado correctamente")

        elif tipo == 'ubicacion':
            ubicacion = get_object_or_404(Ubicacion, idUbicacion=item_id)
            nombre = ubicacion.nombre
            ubicacion.delete()
            messages.success(request, f"Ubicacion '{nombre}' fue eliminado correctamente")

    except ProtectedError as e:
        # Capturar especificamente el error de protección de FK

        # Extraer información útil de error
        protected_objects = e.protected_objects

        # Crear mensaje amigable según el tipo
        if tipo == 'estado':
            # Contar cuantos locales están usando este estado
            locales_count = len(protected_objects)
            messages.error(
                request, 
                f'❌ No se puede eliminar este estado porque está siendo utilizado por '
                f'{locales_count} local(es).'
                f'Primero debes cambiar el estado de esos locales o eliminarlos.'
            )
        elif tipo == 'nivel':
            # Contar cuantos locales están usando este nivel
            locales_count = len(protected_objects)
            messages.error(
                request,
                f'❌ No se puede eliminar este nivel porque está asignado a '
                f'{locales_count} local(es).'
                f'Primero debes reasignar esos locales a otro nivel.'
            )
        elif tipo == 'ubicacion':
            # Contar cuantos locales están usando esta ubicación
            niveles_count = len(protected_objects)

            # Obtener el nombre de los niveles para mostrarlos
            niveles_nombre = [str(obj) for obj in list(protected_objects)[:3]]

            if niveles_count <= 3:
                niveles_lista = ', '.join(niveles_nombre)
                messages.error(
                    request,
                    f'❌ No se puede eliminar esta ubicación porque está siendo utilizada por '
                    f'el/los nivel(es): {niveles_lista}. '
                    f'Primero debes cambiar la ubicación de esos niveles o eliminarlos.'
                )
            else:
                niveles_lista = ', '.join(niveles_nombre)
                messages.error(
                    request,
                    f'❌ No se puede eliminar esta ubicación porque está siendo utilizada por '
                    f'{niveles_count} niveles ({niveles_lista}... y otros). '
                    f'Primero debes cambiar la ubicación de esos niveles o eliminarlos.'
                )
    except Exception as e:
        messages.error(request, f'Error al eliminar el elemento: {str(e)}')

    # Redirigir manteniendo el tab activo
    return redirect(f"{request.path.replace('/eliminar/', '/')}?tab={tab_actual}")