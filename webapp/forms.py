from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import CustomUser, Cliente, ClienteUsuario, Categoria, MedioPago, Tarjeta, Billetera, CuentaBancaria, Cheque
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationForm(UserCreationForm):
    name = forms.CharField(
        label="Nombre",
        widget=forms.TextInput(attrs={
            "placeholder": "Ingrese su nombre",
            "class": "auth-form-input"
        }),
        min_length=2,
        max_length=30
    )
    last_name = forms.CharField(
        label="Apellido",
        widget=forms.TextInput(attrs={
            "placeholder": "Ingrese su apellido",
            "class": "auth-form-input"
        }),
        min_length=2,
        max_length=30
    )
    username = forms.CharField(
        label="Nombre de usuario",
        widget=forms.TextInput(attrs={
            "placeholder": "Elija un nombre de usuario",
            "class": "auth-form-input",
            "id": "username" 
        }),
        min_length=3,
        max_length=30
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "placeholder": "Ingrese su correo",
            "class": "auth-form-input"
        })
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Ingrese una contraseña",
            "class": "auth-form-input",
        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Repita la contraseña",
            "class": "auth-form-input"
        })
    )

    class Meta:
        model = User
        fields = ["name", "last_name", "username", "email", "password1", "password2"]
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Verificar que no contenga caracteres especiales
            if not username.replace('_', '').replace('-', '').isalnum():
                raise forms.ValidationError(
                    "El nombre de usuario solo puede contener letras, números, guiones y guiones bajos."
                )
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar que el email no esté ya registrado
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    "Ya existe una cuenta con este correo electrónico."
                )
        return email

class LoginForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "password"]
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            try:
                user = CustomUser.objects.get(username=username)
                if not user.is_active:
                    raise forms.ValidationError(
                        "Su cuenta no está activa. Por favor revise su correo y confirme su cuenta haciendo clic en el enlace de verificación.",
                        code='inactive'
                    )
            except CustomUser.DoesNotExist:
                pass  # Django manejará el error de autenticación
        
        return super().clean()

# ===========================================
# FORMULARIOS PARA ADMINISTRACIÓN DE CLIENTES
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
    # Validación del RUC 
    # --------------------------
    def clean_ruc(self):
        ruc = self.cleaned_data.get("ruc", "").strip()
        if ruc:
            # El patrón: uno o más dígitos, un guion y un dígito final
            if not re.match(r'^\d+-\d$', ruc):
                raise ValidationError("El RUC debe tener el formato: números-dígito (ej. 1234567-8).")
        return ruc
    
    # --------------------------
    # Validación de correo único
    # --------------------------
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo and Cliente.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Ya existe un cliente con este correo electrónico.")
        return correo

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar que el email no esté ya registrado
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    "Ya existe una cuenta con este correo electrónico."
                )
        return email

class ClienteUpdateForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'tipoCliente', 'nombre', 'razonSocial', 'documento', 'ruc',
            'correo', 'telefono', 'direccion', 'categoria', 'estado'
        ]
        widgets = {
            'tipoCliente': forms.Select(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'razonSocial': forms.TextInput(attrs={'class': 'form-control'}),
            'documento': forms.TextInput(attrs={'class': 'form-control'}),
            'ruc': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'tipoCliente': 'Tipo de Cliente',
            'nombre': 'Nombre',
            'razonSocial': 'Razón Social',
            'documento': 'Documento',
            'ruc': 'RUC',
            'correo': 'Correo Electrónico',
            'telefono': 'Teléfono',
            'direccion': 'Dirección',
            'categoria': 'Categoría',
            'estado': 'Activo',
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if correo and Cliente.objects.filter(correo=correo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un cliente con este correo electrónico.")
        return correo

    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        if documento and Cliente.objects.filter(documento=documento).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Ya existe un cliente con este documento.")
        return documento

#formulario útil para que los usuarios puedan actualizar su información
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]  # add/remove as needed

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


# ===========================================
# FORMULARIOS PARA MEDIOS DE PAGO
# ===========================================

class TarjetaForm(forms.ModelForm):
    class Meta:
        model = Tarjeta
        fields = ['numero_tokenizado', 'banco', 'fecha_vencimiento', 'ultimos_digitos']
        widgets = {
            'numero_tokenizado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número tokenizado (ej: tok_123456789)',
                'required': True
            }),
            'banco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Banco emisor (ej: Banco Nacional)',
                'required': True
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'ultimos_digitos': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Últimos 4 dígitos (ej: 1234)',
                'maxlength': '4',
                'pattern': '[0-9]{4}',
                'required': True
            })
        }
        labels = {
            'numero_tokenizado': 'Número Tokenizado',
            'banco': 'Banco Emisor',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'ultimos_digitos': 'Últimos 4 Dígitos'
        }

    def clean_ultimos_digitos(self):
        ultimos_digitos = self.cleaned_data.get('ultimos_digitos')
        if ultimos_digitos and not ultimos_digitos.isdigit():
            raise ValidationError("Los últimos dígitos deben ser números.")
        if ultimos_digitos and len(ultimos_digitos) != 4:
            raise ValidationError("Debe ingresar exactamente 4 dígitos.")
        return ultimos_digitos


class BilleteraForm(forms.ModelForm):
    class Meta:
        model = Billetera
        fields = ['numero_celular', 'proveedor']
        widgets = {
            'numero_celular': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de celular (ej: 0981234567)',
                'required': True
            }),
            'proveedor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Proveedor (ej: Tigo Money, Zimple)',
                'required': True
            })
        }
        labels = {
            'numero_celular': 'Número de Celular',
            'proveedor': 'Proveedor'
        }

    def clean_numero_celular(self):
        numero_celular = self.cleaned_data.get('numero_celular')
        if numero_celular:
            # Limpiar el número (remover espacios, guiones, etc.)
            numero_limpio = re.sub(r'[^\d]', '', numero_celular)
            if not numero_limpio.isdigit():
                raise ValidationError("El número de celular debe contener solo dígitos.")
            if len(numero_limpio) < 8 or len(numero_limpio) > 15:
                raise ValidationError("El número de celular debe tener entre 8 y 15 dígitos.")
        return numero_celular


class CuentaBancariaForm(forms.ModelForm):
    class Meta:
        model = CuentaBancaria
        fields = ['numero_cuenta', 'banco', 'alias_cbu']
        widgets = {
            'numero_cuenta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de cuenta',
                'required': True
            }),
            'banco': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Banco (ej: Banco Nacional)',
                'required': True
            }),
            'alias_cbu': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alias o CBU',
                'required': True
            })
        }
        labels = {
            'numero_cuenta': 'Número de Cuenta',
            'banco': 'Banco',
            'alias_cbu': 'Alias/CBU'
        }


class ChequeForm(forms.ModelForm):
    class Meta:
        model = Cheque
        fields = ['numero_cheque', 'banco_emisor', 'fecha_vencimiento', 'monto']
        widgets = {
            'numero_cheque': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de cheque',
                'required': True
            }),
            'banco_emisor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Banco emisor (ej: Banco Nacional)',
                'required': True
            }),
            'fecha_vencimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Monto del cheque',
                'step': '0.01',
                'min': '0',
                'required': True
            })
        }
        labels = {
            'numero_cheque': 'Número de Cheque',
            'banco_emisor': 'Banco Emisor',
            'fecha_vencimiento': 'Fecha de Vencimiento',
            'monto': 'Monto'
        }

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto is not None and monto <= 0:
            raise ValidationError("El monto debe ser mayor a 0.")
        return monto


class MedioPagoForm(forms.ModelForm):
    class Meta:
        model = MedioPago
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del medio de pago (ej: Visa Principal)',
                'required': True
            })
        }
        labels = {
            'nombre': 'Nombre del Medio de Pago'
        }