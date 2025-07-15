from django.shortcuts import render, redirect
from boletas.models import BoletaSandbox
from boletas.services.validation import validar_boleta_sandbox
from boletas.services.email_ingestor import procesar_correos
from django.http import HttpResponse

def revisar_boletas(request):
    sandbox_pendientes = BoletaSandbox.objects.filter(estado_validacion = 'Pendiente')
    for boleta in sandbox_pendientes:
        validar_boleta_sandbox(boleta)
    return redirect('boletas:lista_sandbox')

def revisar_correos(request):
    cantidad = procesar_correos()
    return HttpResponse(f"{cantidad} correos procesados")