from django import forms
from negocios.models import Negocio, EstadoNegocio, Categoria
import unicodedata
import re

def quitar_tildes(text):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

class NegocioForm(forms.ModelForm):
    class Meta: 
        model = Negocio
        fields = ['nombre', 'descripcion', 'telefono1', 'telefono2', 'email', 'nit', 'estado', 'categoria']
        labels = {
            'nombre' : 'Nombre Negocio',
            'descripcion' : 'Descripción',
            'email' : 'Correo Electrónico',
            'telefono1' : 'Teléfono 1',
            'telefono2' : 'Teléfono 2',
            'nit' : 'NIT',
            'estado' : 'Estado',
            'categoria' : 'Categoría',
            
        }
        widgets = {
            'nombre' : forms.TextInput(attrs={'class' : 'form-input', 'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 'title': 'Se permiten únicamente letras y espacios'}),
            'descripcion' : forms.TextInput(attrs={'class' : 'form-iput'}),
            'telefono1' : forms.TextInput(attrs={'class' : 'form-input', 'placeholder' : 'Ej: 4444-4444 o 44444444', 'pattern' : r'^\d{8}$|^\d{4}-\d{4}$', 'title' : 'Ingrese un número en formato 44444444 o 4444-4444'}),
            'telefono2' : forms.TextInput(attrs={'class' : 'form-input', 'placeholder' : 'Ej: 4444-4444 o 44444444', 'pattern' : r'^\d{8}$|^\d{4}-\d{4}$', 'title' : 'Ingrese un número en formato 44444444 o 4444-4444'}),
            'email': forms.EmailInput(attrs={'class' : 'form-input', 'placeholder' : 'ejemplo@correo.com'}),
            'nit' : forms.TextInput(attrs={'class' : 'form-input', 'pattern': r'^[0-9]+$', 'title': 'Se permiten únicamente números'})
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")
        return nombre

    def clean_descripcion(self):
        descripcion = self.cleaned_data['descripcion'].strip()
        if descripcion in [None, '']:
            return descripcion
        
        if not re.fullmatch(r"[A-Za-z0-9ÁÉÍÓÚáéíóúÑñ.\s]+", descripcion):
            raise forms.ValidationError("Únicamente se permiten letras, números y espacios.")
        return descripcion

    def clean_nit(self):
        nit = self.cleaned_data['nit']
        # Permitir campo vacío 
        if nit in [None, '']:
            return nit

        if not re.fullmatch(r"[1-9]\d{6,9}", nit):
            raise forms.ValidationError("El NIT debe tener entre 7 y 10 dígitos y no debe comenzar con 0.")
        return nit

    def clean_telefono1(self):
        telefono1 = self.cleaned_data['telefono1']

        if not re.fullmatch(r"(\d{4}-\d{4}|\d{8})", telefono1):
            raise forms.ValidationError("Siga la secuencia permitida en 44444444 o 4444-4444.")    
        return telefono1


    def clean_telefono2(self):
        telefono2 = self.cleaned_data['telefono2']
        if telefono2 in [None, '']:
            return telefono2

        if not re.fullmatch(r"(\d{4}-\d{4}|\d{8})", telefono2):
            raise forms.ValidationError("Siga la secuencia permitida en 44444444 o 4444-4444.")    
        return telefono2



class EstadoNegocioForm(forms.ModelForm):
    class Meta:
        model = EstadoNegocio
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre del estado'
            }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 
                                            'placeholder': 'Ej: Activo', 
                                            'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 
                                            'title': 'Se permiten únicamente letras y espacios.'})
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        nombre_normalizado = quitar_tildes(nombre).lower()

        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")

        # Se normalizan posibles entradas con tildes y se igualan para que no se genera un nuevo ingreso
        for estado in EstadoNegocio.objects.all():
            nombre_existente_normalizado = quitar_tildes(estado.nombre).lower()
            if nombre_existente_normalizado == nombre_normalizado:
                raise forms.ValidationError(f"duplicado: {estado.idEstadoUsuario}")
        
        #Se comprueba si ya existen duplicados en la base de datos, la funcion es devolver un mensaje que pueda ser manejado en 
        #El JS para poder manejarlo, de esta forma se puede devolver en el front lo que se esta ingresando.
        estado_existente = EstadoNegocio.objects.filter(nombre__iexact=nombre).first()
        if estado_existente:
            raise forms.ValidationError(f"duplicado: {estado_existente.idEstadoNegocio}")
        
        #Se comprueba si ya existe un titulo llamado de la misma forma no importando si tiene inicial minuscula o mayuscula
        if EstadoNegocio.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un estado titulado de esa forma.")
        return nombre


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre de la categoría'
            }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 
                                            'placeholder': 'Ej: Abarrotería', 
                                            'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 
                                            'title': 'Se permiten únicamente letras y espacios.'})
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        nombre_normalizado = quitar_tildes(nombre).lower()

        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")
        
        # Se normalizan posibles entradas con tildes y se igualan para que no se genera un nuevo ingreso
        for categoria in Categoria.objects.all():
            nombre_existente_normalizado = quitar_tildes(categoria.nombre).lower()
            if nombre_existente_normalizado == nombre_normalizado:
                raise forms.ValidationError(f"duplicado: {categoria.idCategoria}")

        #Se comprueba si ya existen duplicados en la base de datos, la funcion es devolver un mensaje que pueda ser manejado en 
        #El JS para poder manejarlo, de esta forma se puede devolver en el front lo que se esta ingresando.
        estado_existente = Categoria.objects.filter(nombre__iexact=nombre).first()
        if estado_existente:
            raise forms.ValidationError(f"duplicado: {estado_existente.idCategoria}")
        
        #Se comprueba si ya existe un titulo llamado de la misma forma no importando si tiene inicial minuscula o mayuscula
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un estado titulado de esa forma.")
        return nombre
    

class BusquedaNegocioForm(forms.Form):
    q = forms.CharField(
        required= False,
        label = '',
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por nombre'})
    ) 