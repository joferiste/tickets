from django.shortcuts import render, redirect
from .models import Configuracion, Banco
from django.contrib import messages
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from configuracion.forms import BancoForm

def configuracion_sistema(request):
    config = Configuracion.objects.filter(activo=True).first()
    bancos = Banco.objects.all()
    banco_form = BancoForm

    dias_sin_recargo_opciones = [5, 10, 15, 20]
    mora_porcentaje_opciones = [5, 10, 15, 20]


    if request.method == "POST":
        mora = request.POST.get("mora_porcentaje")
        dias = request.POST.get("dias_sin_recargo")
        banco_id = request.POST.get("banco_principal")

        if not (mora and dias and banco_id):
            messages.error(request, "Debe de completar todos los campos")
        else:
            banco = Banco.objects.get(id=banco_id)
            # Si ya existe una configuracion activa, actualizar
            if config:
                config.mora_porcentaje = mora
                config.dias_sin_recargo = dias
                config.banco_principal = banco
                config.save()
                messages.success(request, "Configuración actualizada con éxito")
            else:
                Configuracion.objects.create(
                    mora_porcentaje = mora,
                    dias_sin_recargo = dias,
                    banco_principal = banco,
                    activo = True
                )
                messages.success(request, "Configuración creada y activada")
                
        return redirect("configuracion:configuracion_sistema")
    return render(request, "configuracion/configuracion_sistema.html", {
        "config": config,
        "bancos": bancos,
        "dias_sin_recargo_opciones": dias_sin_recargo_opciones,
        "mora_porcentaje_opciones": mora_porcentaje_opciones,
        "banco_form": banco_form
    })



def crear_banco(request):
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        
        nombre = data.get('nombre', '').strip()
        numero_cuenta = data.get('numero_cuenta', '').strip()
        
        # Verificar si ya existe el banco con ese nombre y número de cuenta
        try:
            banco_existente = Banco.objects.get(nombre=nombre, numero_cuenta=numero_cuenta)
            return JsonResponse({
                "success": False,
                "duplicado": True,
                "id": banco_existente.id,
                "nombre": str(banco_existente),
            }) 
        except Banco.DoesNotExist:
            pass # Si no existe, proceder con validación de formulario

        # Usar el formulario para validación completa
        form = BancoForm(data)
        if form.is_valid():
            banco = form.save()
            return JsonResponse({
                "success": True,
                "id": banco.id,
                "nombre": str(banco),
            })
        else:
            return JsonResponse({
                "success": False, 
                "errors": form.errors
            })
    return JsonResponse({"success": False, "error": "Petición Inválida"})


def mantenimientos(request):
    bancos = Banco.objects.filter(pk=id).first()
        
