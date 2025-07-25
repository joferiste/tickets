from django import forms
from configuracion.models import Banco
from django.core.exceptions import ValidationError
import re


class BancoForm(forms.ModelForm):
    class Meta:
        model = Banco
        fields = ['nombre', 'numero_cuenta']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Bam', 'title': 'Se permiten únicamente letras y espacios'}),
            'numero_cuenta': forms.TextInput(attrs={'placeholder': '11-111111-11', 'title': 'Se permiten únicamente números y guiones'}),
        } 

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '').strip()
        print("Validando nombre:", nombre)

        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")
        return nombre

    def clean_numero_cuenta(self):
        numero_cuenta = self.cleaned_data.get('numero_cuenta', '').strip()
        print("Validando número de cuenta:", numero_cuenta)
        
        # Validar longitud de la cadena
        if len(numero_cuenta) > 14:
            raise forms.ValidationError("El número de cuenta no debe exceder los 14 caracteres.")
        
        # Validar solo digitos y guiones
        if not re.fullmatch(r"[0-9\-]+", numero_cuenta):
            raise forms.ValidationError("El número de cuenta sólo debe contener dígitos y guiones.")

        # Validar que tenga exactamente dos guions
        if numero_cuenta.count("-") != 2:
            raise forms.ValidationError("El número de cuenta debe de contener dos guiones, (ej. 11-111111-11).")
        
        return numero_cuenta
    
    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get("nombre")
        numero_cuenta = cleaned_data.get("numero_cuenta")

        if self.errors:
            return cleaned_data # Evitar validaciones cruzadas si ya hay errores.

        if nombre and numero_cuenta:
            if Banco.objects.filter(nombre=nombre, numero_cuenta=numero_cuenta).exists():
                raise ValidationError("Ya existe un banco con ese nombre y número de cuenta.")
        return cleaned_data
    

    
