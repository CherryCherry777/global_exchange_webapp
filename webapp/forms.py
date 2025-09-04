from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import CustomUser, Cliente, ClienteUsuario
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={"placeholder": "Ingrese su nombre"})
    )
    last_name = forms.CharField(
        label="Apellido",
        widget=forms.TextInput(attrs={"placeholder": "Ingrese su apellido"})
    )
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={"placeholder": "Elija un nombre de usuario"})
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "Ingrese su correo"})
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Ingrese una contraseña"})
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repita la contraseña"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

class LoginForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "password"]

#formulario útil para que los usuarios puedan actualizar su información
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]  # add/remove as needed


# ===========================================
# FORMULARIOS PARA GESTIÓN DE CLIENTES
# ===========================================

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'razonSocial', 'documento', 'ruc', 'correo', 
            'telefono', 'direccion', 'tipoCliente', 'categoria', 'estado'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'razonSocial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social'}),
            'documento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de documento'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUC'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'tipoCliente': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if self.errors.get(field_name):
                existing_classes = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = existing_classes + ' is-invalid'

    # --------------------------
    # Validación del campo "nombre"
    # --------------------------
    def clean_nombre(self):
        nombre = self.cleaned_data.get("nombre", "").strip()

        if len(nombre) > 150:
            raise ValidationError("El nombre no puede tener más de 150 caracteres.")

        if not re.match(r"^[A-Za-zÁÉÍÓÚÜáéíóúü\s]+$", nombre):
            raise ValidationError(
                "El nombre solo puede contener letras, espacios, acentos y diéresis."
            )

        if re.search(r"\s{2,}", nombre):
            raise ValidationError("El nombre no puede contener múltiples espacios consecutivos.")

        return nombre

    # --------------------------
    # Validación del campo "documento"
    # --------------------------
    def clean_documento(self):
        documento = self.cleaned_data.get("documento", "")

        documento = documento.strip()

        if " " in documento:
            raise ValidationError("El documento no puede contener espacios en blanco.")

        if not documento.isdigit():
            raise ValidationError("El documento debe contener solo números.")

        if documento.startswith("0"):
            raise ValidationError("El documento no puede comenzar con cero.")

        existe = Cliente.objects.filter(documento=documento)
        if self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)

        if existe.exists():
            raise ValidationError("Ya existe un cliente con este documento.")

        return documento

    # --------------------------
    # Validación opcional de RUC (si quieres que sea numérico o cumpla formato)
    # --------------------------
    def clean_ruc(self):
        ruc = self.cleaned_data.get("ruc", "").strip()
        if ruc:
            if not ruc.isdigit():
                raise ValidationError("El RUC debe contener solo números.")
        return ruc


class AsignarClienteForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.filter(estado=True).order_by('nombre'),
        empty_label="Seleccione un cliente",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Cliente"
    )
    
    usuario = forms.ModelChoiceField(
        queryset=CustomUser.objects.filter(is_active=True).order_by('username'),
        empty_label="Seleccione un usuario",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Usuario"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        usuario = cleaned_data.get('usuario')
        
        if cliente and usuario:
            # Verificar si ya existe la asignación
            if ClienteUsuario.objects.filter(cliente=cliente, usuario=usuario).exists():
                raise ValidationError("Esta asignación ya existe.")
        
        return cleaned_data