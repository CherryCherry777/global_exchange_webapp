from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import BilleteraCobro, CuentaBancariaCobro, CustomUser, Cliente, ClienteUsuario, Categoria, Entidad, MedioCobro, MedioPago, Tarjeta, Billetera, CuentaBancaria, TarjetaCobro, TipoCobro, TipoPago, LimiteIntercambio, Currency
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
# MIXIN PARA DESHABILITAR MONEDA
# ===========================================
class MonedaDisabledMixin:
    def disable_moneda(self):
        if 'moneda' in self.fields:
            self.fields['moneda'].disabled = True
            self.fields['moneda'].queryset = Currency.objects.filter(activo=True)
            self.fields['moneda'].widget.attrs.update({'class': 'form-control'})


# ===========================================
# FORMULARIOS PARA MEDIOS DE PAGO
# ===========================================
class TarjetaForm(forms.ModelForm):
    entidad = forms.ModelChoiceField(
        queryset=Entidad.objects.filter(tipo="banco", activo=True),
        label="Banco Emisor",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Tarjeta
        fields = ['numero_tokenizado', 'entidad', 'fecha_vencimiento', 'ultimos_digitos']
        widgets = {
            'numero_tokenizado': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ultimos_digitos': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '4', 'pattern': '[0-9]{4}'}),
        }

    def clean_ultimos_digitos(self):
        ultimos_digitos = self.cleaned_data.get('ultimos_digitos')
        if ultimos_digitos and (not ultimos_digitos.isdigit() or len(ultimos_digitos) != 4):
            raise ValidationError("Debe ingresar exactamente 4 dígitos numéricos.")
        return ultimos_digitos


class BilleteraForm(forms.ModelForm):
    entidad = forms.ModelChoiceField(
        queryset=Entidad.objects.filter(tipo="telefono", activo=True),
        label="Proveedor",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Billetera
        fields = ['numero_celular', 'entidad']
        widgets = {
            'numero_celular': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_numero_celular(self):
        numero_celular = self.cleaned_data.get('numero_celular')
        numero_limpio = re.sub(r'[^\d]', '', numero_celular or "")
        if not numero_limpio.isdigit():
            raise ValidationError("El número de celular debe contener solo dígitos.")
        if len(numero_limpio) < 8 or len(numero_limpio) > 15:
            raise ValidationError("El número de celular debe tener entre 8 y 15 dígitos.")
        return numero_celular


class CuentaBancariaForm(forms.ModelForm):
    entidad = forms.ModelChoiceField(
        queryset=Entidad.objects.filter(tipo="banco", activo=True),
        label="Banco",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CuentaBancaria
        fields = ['numero_cuenta', 'entidad', 'alias_cbu']
        widgets = {
            'numero_cuenta': forms.TextInput(attrs={'class': 'form-control'}),
            'alias_cbu': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MedioPagoForm(forms.ModelForm):
    class Meta:
        model = MedioPago
        fields = ['nombre', 'moneda']


class TipoPagoForm(forms.ModelForm):
    class Meta:
        model = TipoPago
        fields = ["activo", "comision"]
        widgets = {
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "comision": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

# ===========================================
# FORMULARIOS PARA MEDIOS DE COBRO
# ===========================================
class TarjetaCobroForm(TarjetaForm):
    class Meta(TarjetaForm.Meta):
        model = TarjetaCobro


class BilleteraCobroForm(BilleteraForm):
    class Meta(BilleteraForm.Meta):
        model = BilleteraCobro


class CuentaBancariaCobroForm(CuentaBancariaForm):
    class Meta(CuentaBancariaForm.Meta):
        model = CuentaBancariaCobro


class MedioCobroForm(forms.ModelForm):
    class Meta:
        model = MedioCobro
        fields = ['nombre', 'moneda']


class TipoCobroForm(forms.ModelForm):
    class Meta:
        model = TipoCobro
        fields = ["activo", "comision"]
        widgets = {
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "comision": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


# -------------------------
# Edit forms - MÉTODOS DE COBRO
# -------------------------
class TarjetaCobroEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Banco Emisor",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = TarjetaCobro
        fields = ['numero_tokenizado', 'entidad', 'fecha_vencimiento', 'ultimos_digitos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='banco', activo=True)
        self.fields['numero_tokenizado'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_vencimiento'].widget.attrs.update({'class': 'form-control', 'type': 'date'})
        self.fields['ultimos_digitos'].widget.attrs.update({'class': 'form-control'})

    def clean_ultimos_digitos(self):
        ultimos_digitos = self.cleaned_data.get('ultimos_digitos') or ""
        if not ultimos_digitos.isdigit() or len(ultimos_digitos) != 4:
            raise ValidationError("Debe ingresar exactamente 4 dígitos numéricos.")
        return ultimos_digitos


class BilleteraCobroEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Proveedor",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = BilleteraCobro
        fields = ['numero_celular', 'entidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='telefono', activo=True)
        self.fields['numero_celular'].widget.attrs.update({'class': 'form-control'})

    def clean_numero_celular(self):
        numero_celular = self.cleaned_data.get('numero_celular') or ""
        numero_limpio = re.sub(r'[^\d]', '', numero_celular)
        if not numero_limpio.isdigit() or not (8 <= len(numero_limpio) <= 15):
            raise ValidationError("El número de celular debe contener entre 8 y 15 dígitos numéricos.")
        return numero_celular


class CuentaBancariaCobroEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Banco",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CuentaBancariaCobro
        fields = ['numero_cuenta', 'entidad', 'alias_cbu']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='banco', activo=True)
        self.fields['numero_cuenta'].widget.attrs.update({'class': 'form-control'})
        self.fields['alias_cbu'].widget.attrs.update({'class': 'form-control'})


class MedioCobroForm(forms.ModelForm):
    class Meta:
        model = MedioCobro
        fields = ['nombre', 'moneda']


class TipoCobroForm(forms.ModelForm):
    class Meta:
        model = TipoCobro
        fields = ["activo", "comision"]
        widgets = {
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "comision": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }

# -------------------------
# Edit forms - MEDIOS DE PAGO
# -------------------------
class TarjetaEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Banco Emisor",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Tarjeta
        fields = ['numero_tokenizado', 'entidad', 'fecha_vencimiento', 'ultimos_digitos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # deshabilita moneda si aplica
        self.disable_moneda()
        # limitar entidades a bancos activos
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='banco', activo=True)
        # asegurar clases en widgets
        self.fields['numero_tokenizado'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_vencimiento'].widget.attrs.update({'class': 'form-control', 'type': 'date'})
        self.fields['ultimos_digitos'].widget.attrs.update({'class': 'form-control'})

    def clean_ultimos_digitos(self):
        ultimos_digitos = self.cleaned_data.get('ultimos_digitos') or ""
        if not ultimos_digitos.isdigit() or len(ultimos_digitos) != 4:
            raise ValidationError("Debe ingresar exactamente 4 dígitos numéricos.")
        return ultimos_digitos


class BilleteraEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Proveedor",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Billetera
        fields = ['numero_celular', 'entidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='telefono', activo=True)
        self.fields['numero_celular'].widget.attrs.update({'class': 'form-control'})

    def clean_numero_celular(self):
        numero_celular = self.cleaned_data.get('numero_celular') or ""
        numero_limpio = re.sub(r'[^\d]', '', numero_celular)
        if not numero_limpio.isdigit() or not (8 <= len(numero_limpio) <= 15):
            raise ValidationError("El número de celular debe contener entre 8 y 15 dígitos numéricos.")
        return numero_celular


class CuentaBancariaEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Banco",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CuentaBancaria
        fields = ['numero_cuenta', 'entidad', 'alias_cbu']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='banco', activo=True)
        self.fields['numero_cuenta'].widget.attrs.update({'class': 'form-control'})
        self.fields['alias_cbu'].widget.attrs.update({'class': 'form-control'})



# -------------------------
# Edit forms - MÉTODOS DE COBRO
# -------------------------
class TarjetaCobroEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Banco Emisor",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = TarjetaCobro
        fields = ['numero_tokenizado', 'entidad', 'fecha_vencimiento', 'ultimos_digitos']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='banco', activo=True)
        self.fields['numero_tokenizado'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_vencimiento'].widget.attrs.update({'class': 'form-control', 'type': 'date'})
        self.fields['ultimos_digitos'].widget.attrs.update({'class': 'form-control'})

    def clean_ultimos_digitos(self):
        ultimos_digitos = self.cleaned_data.get('ultimos_digitos') or ""
        if not ultimos_digitos.isdigit() or len(ultimos_digitos) != 4:
            raise ValidationError("Debe ingresar exactamente 4 dígitos numéricos.")
        return ultimos_digitos


class BilleteraCobroEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Proveedor",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = BilleteraCobro
        fields = ['numero_celular', 'entidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='telefono', activo=True)
        self.fields['numero_celular'].widget.attrs.update({'class': 'form-control'})

    def clean_numero_celular(self):
        numero_celular = self.cleaned_data.get('numero_celular') or ""
        numero_limpio = re.sub(r'[^\d]', '', numero_celular)
        if not numero_limpio.isdigit() or not (8 <= len(numero_limpio) <= 15):
            raise ValidationError("El número de celular debe contener entre 8 y 15 dígitos numéricos.")
        return numero_celular


class CuentaBancariaCobroEditForm(MonedaDisabledMixin, forms.ModelForm):
    entidad = forms.ModelChoiceField(queryset=Entidad.objects.none(),
                                     label="Banco",
                                     widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = CuentaBancariaCobro
        fields = ['numero_cuenta', 'entidad', 'alias_cbu']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_moneda()
        self.fields['entidad'].queryset = Entidad.objects.filter(tipo='banco', activo=True)
        self.fields['numero_cuenta'].widget.attrs.update({'class': 'form-control'})
        self.fields['alias_cbu'].widget.attrs.update({'class': 'form-control'})


# Form de limites de intercambio

class LimiteIntercambioForm(forms.ModelForm):
    class Meta:
        model = LimiteIntercambio
        fields = ['monto_min', 'monto_max']


class EntidadForm(forms.ModelForm):
    """Formulario para crear una entidad"""
    class Meta:
        model = Entidad
        fields = ["nombre", "tipo", "activo"]


class EntidadEditForm(forms.ModelForm):
    """Formulario para editar una entidad (puede deshabilitar campos si se desea)"""
    class Meta:
        model = Entidad
        fields = ["nombre", "tipo", "activo"]
        # Si querés deshabilitar el tipo al editar:
        # widgets = {
        #     "tipo": forms.Select(attrs={"disabled": True}),
        # }