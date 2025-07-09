from django import forms
from locales.models import Local, EstadoLocal, Nivel, Ubicacion
import unicodedata
import re
from django.core.exceptions import ValidationError


def quitar_tildes(text):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

class LocalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        es_edicion = kwargs.pop('es_edicion', False) # Extraemos el flag
        super().__init__(*args, **kwargs)

        if es_edicion:
            self.fields.pop('estado') # Se quita el campo solo si esta editando

    class Meta:
        model = Local
        fields = ['nombre', 'nivel', 'estado']
        labels = {
            'nombre': 'Nombre del local',
            'nivel': 'Nivel',
            'estado': 'Estado'
        } 
        widgets = {
            'nombre': forms.TextInput(attrs={'class' : 'form-input', 'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 'title': 'Se permiten únicamente letras y espacios'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        #Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios en este campo.")
        return nombre
    
    def clean(self):
        cleaned_data = super().clean()
    
        # Solo validar límite de locales para nuevos registros
        if not self.instance.pk:  # Si no tiene primary key, es un nuevo local
            if Local.objects.count() >= 8:
                raise forms.ValidationError("Ya se alcanzó el máximo de locales permitidos.")
        
        return cleaned_data 
    
    def clean_posicionMapa(self):
        value = self.cleaned_data.get("posicionMapa")
        if value is not None:
            if not isinstance(value, int):
                raise ValidationError("Debe ser un numero entero")
            if value < 1 or value > 8:
                raise ValidationError("Debe estar entre 1 y 8")
            
        #Verificar si existe otro local con esta posicion
        qs = Local.objects.filter(posicionMapa=value)
        if self.instance.pk: # Si esta editando, se excluye asi mismo
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError(f"La posicion {value} ya esta ocupado por otro local")
        
        return value


class EstadoLocalForm(forms.ModelForm):
    class Meta:
        model = EstadoLocal
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre del estado'
        }
        widgets = {
            'nombre': forms.TextInput({'class': 'form-input', 
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
        for estado in EstadoLocal.objects.all():
            nombre_existente_normalizado = quitar_tildes(estado.nombre).lower()
            if nombre_existente_normalizado == nombre_normalizado:
                raise forms.ValidationError(f"duplicado: {estado.idEstado}")
        
        #Se comprueba si ya existen duplicados en la base de datos, la funcion es devolver un mensaje que pueda ser manejado en 
        #El JS para poder manejarlo, de esta forma se puede devolver en el front lo que se esta ingresando.
        estado_existente = EstadoLocal.objects.filter(nombre__iexact=nombre).first()
        if estado_existente:
            raise forms.ValidationError(f"duplicado: {estado_existente.idEstado}")
        
        #Se comprueba si ya existe un titulo llamado de la misma forma no importando si tiene inicial minuscula o mayuscula
        if EstadoLocal.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un estado titulado de esa forma.")
        return nombre
    

class UbicacionForm(forms.ModelForm):
    class Meta:
        model = Ubicacion
        fields = ['nombre']
        labels = {
            'nombre': 'Nombre de la ubicación',
        }
        widgets = {
            'nombre': forms.TextInput({'class': 'form-input', 
                                            'placeholder': 'Ej: Norte', 
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
        for ubicacion in Ubicacion.objects.all():
            nombre_existente_normalizado = quitar_tildes(ubicacion.nombre).lower()
            if nombre_existente_normalizado == nombre_normalizado:
                raise forms.ValidationError(f"duplicado: {ubicacion.idUbicacion}")
        
        #Se comprueba si ya existen duplicados en la base de datos, la funcion es devolver un mensaje que pueda ser manejado en 
        #El JS para poder manejarlo, de esta forma se puede devolver en el front lo que se esta ingresando.
        estado_existente = Ubicacion.objects.filter(nombre__iexact=nombre).first()
        if estado_existente:
            raise forms.ValidationError(f"duplicado: {estado_existente.idUbicacion}")
        
        #Se comprueba si ya existe un titulo llamado de la misma forma no importando si tiene inicial minuscula o mayuscula
        if Ubicacion.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un estado titulado de esa forma.")
        return nombre
    

class NivelForm(forms.ModelForm):
    class Meta:
        model = Nivel
        fields = ['nombre', 'ubicacion', 'costo']
        labels = {
            'nombre': 'Nombre del nivel',
            'ubicacion': 'Ubicación',
            'costo': 'Costo del local'
        }
        widgets = {
            'nombre': forms.TextInput({'class': 'form-input', 
                                            'placeholder': 'Ej: A1', 
                                            'pattern': r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', 
                                            'title': 'Se permiten únicamente letras y espacios'}),
            'costo': forms.TextInput(attrs={'class' : 'form-input', 
                                            'pattern': r'^[0-9]+$', 
                                            'title': 'Se permiten únicamente números'})
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        nombre_normalizado = quitar_tildes(nombre).lower()

        # Validacion por regex (letras y espacios)
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+", nombre):
            raise forms.ValidationError("Únicamente se permiten letras y espacios.")

        # Se normalizan posibles entradas con tildes y se igualan para que no se genera un nuevo ingreso
        for nivel in Nivel.objects.all():
            nombre_existente_normalizado = quitar_tildes(nivel.nombre).lower()
            if nombre_existente_normalizado == nombre_normalizado:
                raise forms.ValidationError(f"duplicado: {nivel.idNivel}")
        
        #Se comprueba si ya existen duplicados en la base de datos, la funcion es devolver un mensaje que pueda ser manejado en 
        #El JS para poder manejarlo, de esta forma se puede devolver en el front lo que se esta ingresando.
        estado_existente = Nivel.objects.filter(nombre__iexact=nombre).first()
        if estado_existente:
            raise forms.ValidationError(f"duplicado: {estado_existente.idNivel}")
        
        #Se comprueba si ya existe un titulo llamado de la misma forma no importando si tiene inicial minuscula o mayuscula
        if Nivel.objects.filter(nombre__iexact=nombre).exists():
            raise forms.ValidationError("Ya existe un estado titulado de esa forma.")
        return nombre
    
    def clean_costo(self):
        costo = self.cleaned_data['costo']
        if not str(costo).isdigit():
            raise forms.ValidationError("El costo debe contener sólo números.")
        return costo
    


class BusquedaLocalForm(forms.Form):
    q = forms.CharField(
        required= False,
        label = '',
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre'
        })
    )

class AsignarPosicionMapaForm(forms.Form):
    local = forms.ModelChoiceField(queryset=Local.objects.all(), widget=forms.HiddenInput())
    posicionMapa = forms.ChoiceField(label= "Posición")

    def __init__(self, *args, posiciones_ocupadas=None, **kwargs):
        super().__init__(*args, **kwargs)
        posiciones_disponibles = [(str(i), f"Posicion {i}") for i in range(1,9) if i not in posiciones_ocupadas]
        self.fields['posicionMapa'].choices = posiciones_disponibles