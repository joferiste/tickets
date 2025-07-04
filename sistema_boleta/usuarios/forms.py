from django import forms
from django.core.exceptions import ValidationError
import re
from usuarios.models import Usuario, EstadoUsuario
import unicodedata
from negocios.models import Negocio

def quitar_tildes(text):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'direccionCompleta', 'dpi', 'nit', 'fechaNacimiento', 'telefono1', 'telefono2', 'email', 'estado']
        labels = {
            'nombre' : 'Nombre Completo',
            'direccionCompleta' : 'Dirección Completa',
            'fechaNacimiento' : 'Fecha de Nacimiento',
            'telefono1' : 'Teléfono 1',
            'telefono2' : 'Teléfono 2',
            'email' : 'Correo Electrónico',
            'dpi' : 'DPI',
            'nit' : 'NIT'
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 'title': 'Se permiten únicamente letras y espacios'}),
            'direccionCompleta': forms.TextInput(attrs={'class': 'form-input'}),
            'fechaNacimiento': forms.DateInput(attrs={'class': 'form-input', 'type' : 'date'}, format='%Y-%m-%d'),
            'telefono1': forms.TextInput(attrs={'class' : 'form-input', 'placeholder' : 'Ej: 4444-4444 o 44444444', 'pattern' : r'^\d{8}$|^\d{4}-\d{4}$', 'title' : 'Ingrese un número en formato 44444444 o 4444-4444'}),
            'telefono2': forms.TextInput(attrs={'class' : 'form-input', 'placeholder' : 'Ej: 4444-4444 o 44444444', 'pattern' : r'^\d{8}$|^\d{4}-\d{4}$', 'title' : 'Ingrese un número en formato 44444444 o 4444-4444'}),
            'email': forms.EmailInput(attrs={'class' : 'form-input', 'placeholder' : 'ejemplo@correo.com'}),
            'dpi': forms.TextInput(attrs={'class': 'form-input', 'pattern': r'^[0-9]+$', 'title': 'Se permiten únicamente números'}),
            'nit': forms.TextInput(attrs={'class': 'form-input', 'pattern': r'^[0-9]+$', 'title': 'Se permiten únicamente números'})
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")
        return nombre

    def clean_nit(self):
        nit = self.cleaned_data['nit']
        # Permitir campo vacío 
        if nit in [None, '']:
            return nit

        if not re.fullmatch(r"[1-9]\d{6,9}", nit):
            raise forms.ValidationError("El NIT debe tener entre 7 y 10 dígitos y no debe comenzar con 0.")
        return nit
    
    def clean_dpi(self):
        dpi = self.cleaned_data['dpi']
        
        if not re.fullmatch(r"[1-9]\d{12}", dpi):
            raise forms.ValidationError("El DPI debe tener 13 dígitos y no debe comenzar con 0.")
        return dpi



class EstadoUsuarioForm(forms.ModelForm):
    class Meta:
        model = EstadoUsuario
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre estado'
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 
                                            'placeholder': 'Ej. Activo', 
                                            'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 
                                            'title': 'Se permiten únicamente letras y espacios'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        nombre_normalizado = quitar_tildes(nombre).lower()

        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")

        # Se normalizan posibles entradas con tildes y se igualan para que no se genera un nuevo ingreso
        for estado in EstadoUsuario.objects.all():
            nombre_existente_normalizado = quitar_tildes(estado.nombre).lower()
            if nombre_existente_normalizado == nombre_normalizado:
                raise forms.ValidationError(f"duplicado: {estado.idEstadoUsuario}")
            
        #Se comprueba si ya existen duplicados en la base de datos, la funcion es devolver un mensaje que pueda ser manejado en 
        #El JS para poder manejarlo, de esta forma se puede devolver en el front lo que se esta ingresando.
        estado_existente = EstadoUsuario.objects.filter(nombre__iexact=nombre).first()
        if estado_existente:
            raise forms.ValidationError(f"duplicado: {estado_existente.idEstadoUsuario}")
        
        #Se comprueba si ya existe un titulo llamado de la misma forma no importando si tiene inicial minuscula o mayuscula
        if EstadoUsuario.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un estado titulado de esa forma.")
        return nombre
    

class BusquedaUsuarioForm(forms.Form):
    q = forms.CharField(
        required= False,
        label = '',
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por nombre'})
    )


class AsignarNegocioForm(forms.Form):
    usuario = forms.ModelChoiceField(queryset=Usuario.objects.all(), label="Usuario")
    negocio = forms.ModelChoiceField(
        queryset=Negocio.objects.filter(usuario__isnull=True), label="Negocio sin asignar"
    )