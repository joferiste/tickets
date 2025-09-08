from django import forms
from boletas.models import Boleta, TipoPago

class ProcesarBoletaForm(forms.ModelForm):
    class Meta:
        model = Boleta
        fields = ['monto', 'numeroBoleta', 'numeroDeCuenta', 'tipoPago']
        widgets = {
            'monto': forms.TextInput(attrs={'class': 'form-control'}),
            'numeroBoleta': forms.TextInput(attrs={'class': 'form-control'}),
            'numeroDeCuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'tipoPago': forms.Select(attrs={'class': 'form-select'}),
        }