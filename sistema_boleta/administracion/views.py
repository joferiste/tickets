from django.shortcuts import render
from boletas.views import BoletaSandbox
from boletas.services.email_ingestor import procesar_correos
from django.http import HttpResponse

def boletas_sandbox(request):
    boletas = BoletaSandbox.objects.all().order_by('-fecha_recepcion')
    return render(request, 'administracion/administracion.html', {
        'boletas': boletas
    })

def revisar_correos(request):
    cantidad = procesar_correos()
    return HttpResponse(f"{cantidad} correos procesados")