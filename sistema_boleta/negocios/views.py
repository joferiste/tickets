from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from negocios.forms import NegocioForm, EstadoNegocioForm, CategoriaForm, BusquedaNegocioForm, AsignarLocalForm
from negocios.models import EstadoNegocio, Categoria, Negocio
from locales.models import Local, OcupacionLocal, EstadoLocal   
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic.detail import DetailView
from boletas.models import Boleta, BoletaSandbox
from transacciones.models import Transaccion
from recibos.models import Recibo
import json


def CreacionNegocios(request):
    if request.method == 'POST':
        form = NegocioForm(request.POST)
        estado_form = EstadoNegocioForm() 
        categoria_form = CategoriaForm()

        if form.is_valid():
            form.save()
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
    if request.method == "POST":
        form = BusquedaNegocioForm(request.POST)
    else:
        form = BusquedaNegocioForm()

    negocio = Negocio.objects.all()

    if form.is_valid():
        q = form.cleaned_data.get('q')
        if q:
            negocios = negocios.filter(nombre__icontains=q)

    return render(request, 'negocios/visualizar_negocios.html', {'form': form, 'negocios': negocio})


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
        return JsonResponse({"success": False, "error": "id del Negocio no proporcionado"})

    negocio = get_object_or_404(Negocio, idNegocio = negocio_id)
    form = NegocioForm(request.POST, instance=negocio)

    if form.is_valid():
        form.save()
            # Construccion del diccionario con los campos que necesitamos actualizar en el DOM
        return JsonResponse({
            "success": True, 
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
        return JsonResponse({"success": False, "html": html_form})


@require_POST
def delete_negocio(request):
    negocio_id = request.POST.get('id')
    negocio = get_object_or_404(Negocio, idNegocio=negocio_id)

    try:
        negocio.delete()

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

    # Finaliza la Ocupacion
    ocupacion.fecha_fin = timezone.now().date()
    ocupacion.save()

    # Cambia el estado del local a 'Disponible'
    estado_disponible = get_object_or_404(EstadoLocal, nombre__iexact="Disponible")
    local = ocupacion.local
    local.estado = estado_disponible
    local.save()

    messages.info(request, f"Local {local.nombre} fue desasignado del negocio {ocupacion.negocio.nombre} y marcado como Disponible")
    return redirect('negocios:negocio_local')


class PerfilNegocioView(DetailView): 
    model = Negocio
    template_name = 'negocios/perfil.html'
    context_object_name = 'negocio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        negocio = self.get_object()
        context['sandbox'] = BoletaSandbox.objects.filter(metadata__negocio_id=negocio.idNegocio).order_by("fecha_recepcion")
        context['boletas'] = Boleta.objects.filter(negocio=negocio)
        context['transacciones'] = Transaccion.objects.filter(boleta__negocio=negocio)
        context['recibos'] = Recibo.objects.filter(transaccion__boleta__negocio=negocio)
        context['ocupaciones'] = OcupacionLocal.objects.filter(negocio=negocio, fecha_fin__isnull=True)
        return context