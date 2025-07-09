from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from locales.forms import LocalForm, EstadoLocalForm, NivelForm, UbicacionForm, BusquedaLocalForm, AsignarPosicionMapaForm
from locales.models import Nivel, EstadoLocal, Ubicacion, Local
import json
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.db.models.deletion import ProtectedError


def crear_local(request):
    max_locales = 8
    total_locales = Local.objects.count()
    bloqueado = total_locales >= max_locales
    
    if request.method == 'POST':
        if bloqueado:
            messages.warning(request, '⚠️ Ya se alcanzó el máximo de locales permitidos (8). Elimine uno para crear otro.')
            return redirect('locales:create_local')
        

        form = LocalForm(request.POST)
        estado_form = EstadoLocalForm()
        nivel_form = NivelForm()
        ubicacion_form = UbicacionForm()

        if form.is_valid():
            form.save()
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
    if request.method == "POST":
        form = BusquedaLocalForm(request.POST)
    else:
        form = BusquedaLocalForm()

    locales = Local.objects.all()

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            locales = locales.filter(nombre__icontains=q)

    return render(request, 'locales/visualizar_locales.html', {'form': form, 'locales': locales})



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
        return JsonResponse({"success": False, "error":"id de local no proporcionado"})
    
    local = get_object_or_404(Local, idLocal=local_id)

    #Nuevamente, es una edicion
    form = LocalForm(request.POST, instance=local, es_edicion=True)

    if form.is_valid():
        form.save()
        return JsonResponse({
            "success": True,
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
        return JsonResponse({"success": False, "html": html})


@require_POST
def delete_local(request):
    local_id = request.POST.get('id')
    local = get_object_or_404(Local, idLocal=local_id)

    try:
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
                local.posicionMapa = posicion
                local.save()
                messages.success(request, f"Se asignó la posición {posicion} al local {local.nombre}.")
                return redirect('locales:orden_local')
            
        elif 'desasignar_posicion' in request.POST:
            local_id = request.POST.get('local_id')
            local = get_object_or_404(Local, pk=local_id)
            posicion = local.posicionMapa
            local.posicionMapa = None
            local.save()
            messages.info(request, f"Se desasignó la posición {posicion} del local {local.nombre}.")
            return redirect('locales:orden_local')
        
        elif 'reiniciar' in request.POST:
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
    local.posicionMapa = None
    local.save()
    
    messages.success(request, f"La posición del local {local.nombre} ha sido desasignada.")
    return redirect('locales:orden_local')  # Ajusta el redirect según tu nombre de vista