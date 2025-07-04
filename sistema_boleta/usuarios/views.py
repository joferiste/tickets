from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from usuarios.forms import UsuarioForm, EstadoUsuarioForm, BusquedaUsuarioForm, AsignarNegocioForm
from django.http import JsonResponse
from usuarios.models import EstadoUsuario, Usuario
from negocios.models import Negocio
import json
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError
from django.template.loader import render_to_string

def CreacionUsuarios(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        estado_form = EstadoUsuarioForm()

        if form.is_valid():
            form.save() 
            messages.success(request, '✅ Usuario creado correctamente.')
            return redirect('usuarios:create_usuario')
    else:
        form = UsuarioForm()
        estado_form = EstadoUsuarioForm()
    return render(request, 'usuarios/usuarios.html', {'form': form, 'estado_form': estado_form})

def crear_estado(request):
    form = UsuarioForm()
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "errors": {"general": ["Datos invalidos"]}})
        
        estado_form = EstadoUsuarioForm(data)
        if estado_form.is_valid():
            nuevo_estado = estado_form.save()
            return JsonResponse({
                "success": True,
                "id": nuevo_estado.idEstadoUsuario,
                "nombre": nuevo_estado.nombre
            })
        else:
            errors = estado_form.errors
            nombre_errors = errors.get('nombre')
            if nombre_errors and nombre_errors[0].startswith("duplicado:"):
                estado_id = nombre_errors[0].split(":")[1]
                estado_existente = EstadoUsuario.objects.get(idEstadoUsuario=estado_id)
                return JsonResponse({
                    "success": False,
                    "duplicado":True,
                    "id": estado_existente.idEstadoUsuario,
                    "nombre": estado_existente.nombre
            })
        return JsonResponse({"success": False, "errors": errors})
        
    estado_form = EstadoUsuarioForm()
    return render(request, 'usuarios/usuarios.html', {'form': form, 'estado_form': estado_form})


def visualizar_usuario(request):
    if request.method == "POST":
        form = BusquedaUsuarioForm(request.POST)
    else:
        form = BusquedaUsuarioForm()

    usuarios = Usuario.objects.all()
    estados = EstadoUsuario.objects.all()

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            usuarios = usuarios.filter(nombre__icontains=q)

    return render(request, 'usuarios/visualizar_usuarios.html', {'form': form, 'usuarios': usuarios, 'estados': estados}) 


def editar_usuario(request, id):
    usuario = get_object_or_404(Usuario, idUsuario=id)
    form = UsuarioForm(instance=usuario)

    html = render_to_string("usuarios/form_editar_usuarios.html", {
        'form': form,
        'usuario': usuario
    }, request=request)
    
    return JsonResponse({'html':html}) 


@require_POST 
def actualizar_usuario(request):
    usuario_id = request.POST.get('id')
    
    if not usuario_id:
        return JsonResponse({"success": False, "error":"id de usuario no proporcionado"})
    
    usuario = get_object_or_404(Usuario, idUsuario = usuario_id)
    form = UsuarioForm(request.POST, instance=usuario)

    if form.is_valid():
        form.save()
        return JsonResponse({
            "success": True,
            "usuario": {
                "id": usuario.idUsuario,
                "nombre": usuario.nombre,
                'direccionCompleta': usuario.direccionCompleta,
                'dpi': usuario.dpi,
                'nit': usuario.nit,
                'telefono1': usuario.telefono1,
                'telefono2': usuario.telefono2,
                'email': usuario.email,
                'fechaNacimiento': usuario.fechaNacimiento,
                "estado": str(usuario.estado),
            }
        })
    else:
        print(f"Form errores: {form.errors}")
        html = render_to_string("usuarios/form_editar_usuarios.html", {
            "form": form,
            "usuario": usuario
        }, request=request)
        return JsonResponse({"success": False, "html": html})


@require_POST
def delete_usuario(request):
    usuario_id = request.POST.get('id')
    usuario = get_object_or_404(Usuario, idUsuario=usuario_id)

    try:
        usuario.delete()

        return JsonResponse({
            "success":True,
            "usuario_id": usuario_id
        })       
    except ProtectedError:
        return JsonResponse({
            "success": False,
            "error": "❌ No se puede eliminar este usuario porque está asignado a otros elementos."
        })


def usuario_negocio(request):
    usuarios = Usuario.objects.all()
    negocios = Negocio.objects.filter(usuario__isnull=False)

    if request.method == 'POST':
        form = AsignarNegocioForm(request.POST)
        if form.is_valid():
            usuario = form.cleaned_data['usuario']
            negocio = form.cleaned_data['negocio']
            negocio.usuario = usuario
            negocio.save()
            messages.success(request, f"Negocio {negocio.nombre} asignado a {usuario.nombre}.")
            return redirect('usuarios:usuario_negocio')
    else:
        form = AsignarNegocioForm()

    context = {
        'form': form,
        'negocios': negocios
    }
    return render(request, 'usuarios/usuario_negocio.html', context)


def desasignar_negocio(request, negocio_id):
    negocio = get_object_or_404(Negocio, pk=negocio_id)

    # Guardando nombre antes de eliminar
    usuario_nombre = negocio.usuario.nombre if negocio.usuario else "Desconocido"

    negocio.usuario = None
    negocio.save()

    messages.info(request, f"Negocio {negocio.nombre} ha sido desasignado del usuario {usuario_nombre}.")
    return redirect('usuarios:usuario_negocio')
