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
        
        # Contar digitos (sin guiones)
        solo_digitos = numero_cuenta.replace("-", "")
        if not solo_digitos.isdigit() or not (9 <= len(solo_digitos) <= 11):
            raise forms.ValidationError("El numero de cuenta debe de tener entre 9 y 11 digitos")

        # Validar que si hay guiones, tenga al menod dos 
        cantidad_guiones = numero_cuenta.count("-")
        if cantidad_guiones > 0 and cantidad_guiones < 2:
            raise forms.ValidationError("Si usas guiones, el numero de cuenta debe contener al menos 2 (ej. 11-111111-11).")
        
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
    

    
