from django import forms
from django.core.exceptions import ValidationError
import re
from .models import Cliente


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
