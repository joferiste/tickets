from django.shortcuts import render, get_object_or_404
from boletas.views import BoletaSandbox
from boletas.services.email_ingestor.email_ingestor import procesar_correos
from django.http import JsonResponse
from django.template.loader import render_to_string

def boletas_sandbox(request):
    boletas = BoletaSandbox.objects.all().order_by('-fecha_recepcion')
    return render(request, 'administracion/administracion.html', {
        'boletas': boletas
    })



def revisar_correos(request):
    if request.method == 'POST':
        try:
            cantidad = procesar_correos()
            if cantidad is None:
                cantidad = 0
            return JsonResponse({"mensaje": f"{cantidad} correos procesados."}, status=200)
        except Exception as e:
            print(f"[ERROR] Fallo al procesar correos: {e}")
            return JsonResponse({"mensaje": "Error interno al procesar el correo."}, status=500)
    return JsonResponse({'mensaje': 'Método no permitido'}, status=405)

def boleta_detalle(request, boleta_id):
    boleta = get_object_or_404(BoletaSandbox, id=boleta_id)

    # Marcar como leído si no lo está
    if not boleta.leido:
        boleta.leido = True
        boleta.save(update_fields=['leido'])
        
    return render(request, 'administracion/boleta_detalle.html', {'boleta':boleta})

def boletas_sandbox_parcial(request):
    boletas = BoletaSandbox.objects.all().order_by('-fecha_recepcion')
    html = render_to_string('administracion/_tabla_boletas.html', {'boletas':boletas})
    return JsonResponse({'html':html})