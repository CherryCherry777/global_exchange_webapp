import secrets
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
import secrets

#Las clases van aqui
#Los usuarios heredan AbstractUser
class CustomUser(AbstractUser):
    
    """
    CustomUser model extends Django's AbstractUser to enforce unique email addresses.
    Attributes:
        email (EmailField): The user's email address. Must be unique.
    Methods:
        __str__(): Returns the username as the string representation of the user.
    """
    email = models.EmailField(unique=True)

    receive_exchange_emails = models.BooleanField(
        default=True,
        verbose_name="Recibir notificaciones de tasas de cambio"
    )

    unsubscribe_token = models.CharField(max_length=64, blank=True, null=True)

    class Meta:
        permissions = [
            ("access_admin_panel", "Can access admin panel"),
            ("access_analyst_panel", "Can access analyst panel"),
        ]

    def __str__(self):
        return self.username


class Role(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name="role")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.group.name
    
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="Código")
    name = models.CharField(max_length=50, verbose_name="Nombre")
    symbol = models.CharField(max_length=5, verbose_name="Símbolo")
    base_price = models.DecimalField(max_digits=23, decimal_places=8, verbose_name="Precio Base", default=1.0)
    comision_venta = models.DecimalField(max_digits=23, decimal_places=8, verbose_name="Comisión por venta", default=1.0)
    comision_compra = models.DecimalField(max_digits=23, decimal_places=8, verbose_name="Comisión por compra", default=1.0)
    decimales_cotizacion = models.PositiveSmallIntegerField(
        verbose_name="Decimales para tasa de cambio",
        default=4,
        help_text="Número de decimales para mostrar y almacenar la tasa de cambio (0-8)"
    )
    decimales_monto = models.PositiveSmallIntegerField(
        verbose_name="Decimales para montos",
        default=2,
        help_text="Número de decimales para mostrar y almacenar los montos (0-8)"
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        if not (0 <= self.decimales_cotizacion <= 8):
            raise ValidationError({'decimales_cotizacion': 'El valor debe estar entre 0 y 8.'})
        if not (0 <= self.decimales_monto <= 8):
            raise ValidationError({'decimales_monto': 'El valor debe estar entre 0 y 8.'})
    flag_image = models.ImageField(upload_to="currency_flags/", verbose_name="Bandera (255x135)", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"
    

#Denominaciones de monedas
class CurrencyDenomination(models.Model):
    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name="denominations",
        verbose_name="Moneda"
    )
    # Valor del billete/moneda
    value = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        verbose_name="Valor",
        help_text="Valor numérico de la denominación (ej: 100.00)"
    )
    # Billete o Moneda
    type = models.CharField(
        max_length=20,
        choices=[("bill", "Billete"), ("coin", "Moneda")],
        default="bill",
        verbose_name="Tipo"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        verbose_name = "Denominación de Moneda"
        verbose_name_plural = "Denominaciones de Moneda"
        ordering = ["currency", "-value"]
        unique_together = ("currency", "value")

    def __str__(self):
        return f"{self.currency.code} {self.value} ({self.get_type_display()})"


class CurrencyHistory(models.Model):
    currency = models.ForeignKey(
        "Currency", on_delete=models.CASCADE, related_name="histories"
    )
    date = models.DateField(verbose_name="Fecha de la cotización")
    compra = models.DecimalField(max_digits=23, decimal_places=8, verbose_name="Tasa de compra")
    venta = models.DecimalField(max_digits=23, decimal_places=8, verbose_name="Tasa de venta")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Histórico de moneda"
        verbose_name_plural = "Históricos de monedas"
        ordering = ["-date", "currency"]
        unique_together = ("currency", "date")  # 🔹 No duplicar la misma moneda en la misma fecha

    def __str__(self):
        return f"{self.currency.code} - {self.date} (C:{self.compra}, V:{self.venta})"


# --------------------------------------------------------------
# Modelo de la tabla cliente para migración en la tabla de datos
# --------------------------------------------------------------
class Cliente(models.Model):  # Definimos el modelo Cliente, que representa la tabla 'clientes'

    # Campo que define el tipo de cliente: persona física o jurídica.
    tipoCliente = models.CharField(
        max_length=50,  # Longitud máxima de 50 caracteres
        choices=[
            ('persona_fisica', 'Persona Física'),     # Opción 1: Persona física
            ('persona_juridica', 'Persona Jurídica'), # Opción 2: Persona jurídica
        ],
        verbose_name="Tipo de Cliente"  # Nombre más amigable para mostrar en formularios y el admin
    )

    # Nombre del cliente
    nombre = models.CharField(
        max_length=150,            # Hasta 150 caracteres
        verbose_name="Nombre"      # Etiqueta descriptiva
    )

    # Razón social, solo aplicable para clientes jurídicos, por eso es opcional
    razonSocial = models.CharField(
        max_length=150,            # Hasta 150 caracteres
        null=True,                 # Permite que el valor sea NULL en la base de datos
        blank=True,                # Permite que el formulario lo deje vacío
        verbose_name="Razón Social"
    )

    # Documento del cliente (ej: cédula, DNI, etc.)
    documento = models.CharField(
        max_length=20,             # Hasta 20 caracteres
        verbose_name="Documento"
    )

    # RUC (Registro Único del Contribuyente), puede ser opcional
    ruc = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="RUC"
    )

    # Correo electrónico, debe ser único
    correo = models.EmailField(
        max_length=150,
        unique=True,                # No se permiten correos duplicados
        verbose_name="Correo Electrónico"
    )

    # Número de teléfono del cliente
    telefono = models.CharField(
        max_length=30,
        verbose_name="Teléfono"
    )

    # Dirección del cliente
    direccion = models.CharField(
        max_length=200,
        verbose_name="Dirección"
    )
    
    # Relación con la tabla Categoria
    categoria = models.ForeignKey(
        "Categoria",
        on_delete=models.PROTECT,  # Evita que se elimine una categoría si tiene clientes
        related_name="clientes",
        verbose_name="Categoría"
    )

    # Estado del cliente: activo (True) o inactivo (False)
    estado = models.BooleanField(
        default=True,              # Por defecto, todos los clientes son activos
        verbose_name="Activo"
    )

    # Fecha y hora en que se registró el cliente. Se genera automáticamente al crear el registro.
    fechaRegistro = models.DateTimeField(
        auto_now_add=True,         # Se asigna solo al crear el registro
        verbose_name="Fecha de Registro"
    )

    # ID del cliente asociado en stripe a este
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)

    # Representación del objeto en formato de texto
    def __str__(self):
        return f"{self.nombre} ({self.tipoCliente})"
        # Devuelve el nombre y el tipo de cliente para identificarlo fácilmente

    # Configuraciones adicionales para el modelo
    class Meta:
        db_table = "clientes"                    # Nombre explícito de la tabla en la base de datos
        verbose_name = "Cliente"                 # Nombre singular para mostrar en el admin
        verbose_name_plural = "Clientes"         # Nombre plural para mostrar en el admin
        ordering = ["-fechaRegistro"]            # Orden por defecto: registros más recientes primero


# -----------------------------------------------------------------
# Modelo de la tabla intermedia que relaciona usuarios con clientes
# -----------------------------------------------------------------
class ClienteUsuario(models.Model):  # Define la relación entre Cliente y Usuario

    # Relación con la tabla Cliente
    cliente = models.ForeignKey(
        Cliente,                   # Modelo al que se relaciona
        on_delete=models.CASCADE   # Si se elimina el cliente, se eliminan las relaciones asociadas
    )

    # Relación con la tabla Usuario (usa AUTH_USER_MODEL para mayor flexibilidad)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Usa el modelo de usuario definido en settings
        on_delete=models.CASCADE   # Si se elimina el usuario, se elimina la relación
    )

    # Fecha y hora en que se asignó el cliente a un usuario
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,         # Se asigna automáticamente al crear la relación
        verbose_name="Fecha de Asignación"
    )

    # Representación en formato de texto de la relación
    def __str__(self):
        return f"Cliente: {self.cliente.nombre} - Usuario: {self.usuario.username}"

    # Configuraciones adicionales para el modelo
    class Meta:
        db_table = "cliente_usuario"                   # Nombre explícito de la tabla
        unique_together = ("cliente", "usuario")       # Evita que un mismo usuario se asigne dos veces al mismo cliente
        verbose_name = "Cliente-Usuario"               # Nombre singular para admin
        verbose_name_plural = "Clientes-Usuarios"      # Nombre plural para admin

# -------------------------------------
# Modelo de la tabla de segmentaciones
# -------------------------------------
class Categoria(models.Model):
    # Campo para el nombre de la categoría
    # - máx. 25 caracteres
    # - único (no se pueden repetir nombres)
    # - con un label más descriptivo en el admin/django forms
    nombre = models.CharField(
        max_length=25,
        unique=True,
        verbose_name="Nombre de la categoría"
    )

    # Campo para el descuento asociado a la categoría
    # - número decimal con hasta 4 dígitos en total y 3 decimales (ej: 0.200 = 20%, 0.050 = 5%)
    # - validadores que limitan el rango: mínimo 0 (0%) y máximo 1 (100%)
    # - label descriptivo en el admin/django forms
    descuento = models.DecimalField(
        max_digits=4, 
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Descuento"
    )

    class Meta:
        # Nombre singular y plural en el admin de Django
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        # Ordenar las categorías por el campo "nombre" al consultarlas
        ordering = ["id"]

    def __str__(self):
        # Representación en string del objeto (ej: "VIP (20%)")
        # Muestra el nombre y el descuento en porcentaje sin decimales
        return f"{self.nombre} ({self.descuento * 100:.0f}%)"

# ------------------------------
# Nueva clase Entidad
# ------------------------------
"""
class Entidad(models.Model):
    TIPO_CHOICES = [
        ("banco", "Banco"),
        ("telefono", "Entidad Telefónica"),
    ]

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Entidad")
    activo = models.BooleanField(default=True, verbose_name="Activo")  

    class Meta:
        db_table = "entidades"
        verbose_name = "Entidad"
        verbose_name_plural = "Entidades"

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
"""
class Entidad(models.Model):
    TIPO_CHOICES = [
        ("banco", "Banco"),
        ("telefono", "Entidad Telefónica"),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    # 🔹 Managers dinámicos según tipo
    @classmethod
    def telefonicas(cls):
        return cls.objects.filter(tipo="telefono", activo=True)

    @classmethod
    def bancarias(cls):
        return cls.objects.filter(tipo="banco", activo=True)


# -------------------------------------
# Modelo de medios de pago genérico
# -------------------------------------
class MedioPago(models.Model):
    # Opciones predefinidas para los medios de pago
    TIPO_CHOICES = [
        ('tarjeta_nacional', 'Tarjeta de Débito/Crédito Nacional'),
        ('tarjeta_internacional', 'Tarjeta de Débito/Crédito Internacional (Stripe)'),
        ('billetera', 'Billetera Electrónica'),
        ('cuenta_bancaria', 'Cuenta Bancaria'),
    ]
    
    # Relación con el cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="medios_pago",
        verbose_name="Cliente"
    )
    
    # Tipo de medio de pago
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Medio de Pago"
    )
    
    # Nombre descriptivo del medio de pago (ej: "Visa Principal", "Mercado Pago")
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Medio de Pago"
    )
    
    # Estado del medio de pago (activo/inactivo)
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    
    # Fecha de creación
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    # Fecha de última actualización
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )
    
    tipo_pago = models.ForeignKey(
        "TipoPago",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tipo de Pago Global",
        help_text="Configuración global de activación y comisión"
    )

    
    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        null=True,
        blank=True,
        #editable=False,
        default=None #ID de la moneda por defecto
    )
    

    class Meta:
        db_table = "medios_pago"
        verbose_name = "Medio de Pago"
        verbose_name_plural = "Medios de Pago"
        ordering = ["cliente__nombre", "tipo", "nombre"]
        unique_together = ("cliente", "tipo", "nombre")
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.get_tipo_display()} - {self.nombre}"


# -------------------------------------
# Modelos específicos por tipo de medio de pago
# -------------------------------------
class TarjetaNacional(models.Model):
    """
    Representa una tarjeta nacional (emitida por un banco local).
    Asociada a un MedioPago de tipo 'tarjeta_nacional'.
    """
    medio_pago = models.OneToOneField(
        "MedioPago",
        on_delete=models.CASCADE,
        related_name="tarjeta_nacional",
        verbose_name="Medio de Pago"
    )
    numero_tokenizado = models.CharField(max_length=50, verbose_name="Número Tokenizado")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    ultimos_digitos = models.CharField(max_length=4, verbose_name="Últimos 4 Dígitos")

    
    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "banco"},
        verbose_name="Banco Emisor",
        null=True
    )

    moneda = models.ForeignKey("Currency", on_delete=models.PROTECT, verbose_name="Moneda", editable=False, default=1)

    class Meta:
        db_table = "tarjetas_nacionales"
        verbose_name = "Tarjeta Nacional"
        verbose_name_plural = "Tarjetas Nacionales"

    def __str__(self):
        return f"{self.medio_pago.nombre} - ****{self.ultimos_digitos} ({self.entidad.nombre})"


class TarjetaInternacional(models.Model):
    """
    Representa una tarjeta internacional (emitida y tokenizada por Stripe).
    Asociada a un MedioPago de tipo 'tarjeta_internacional'.
    """
    medio_pago = models.OneToOneField(
        "MedioPago",
        on_delete=models.CASCADE,
        related_name="tarjeta_internacional",
        verbose_name="Medio de Pago"
    )

    # ID del Payment Method en Stripe
    stripe_payment_method_id = models.CharField(
        max_length=100,
        verbose_name="ID de Payment Method en Stripe"
    )

    # Últimos 4 dígitos de la tarjeta
    ultimos_digitos = models.CharField(max_length=4, verbose_name="Últimos 4 Dígitos")

    # Fecha de vencimiento
    exp_month = models.PositiveSmallIntegerField(verbose_name="Mes de Vencimiento")
    exp_year = models.PositiveSmallIntegerField(verbose_name="Año de Vencimiento")
    
    class Meta:
        db_table = "tarjetas_internacionales"
        verbose_name = "Tarjetas Internacionales"
        verbose_name_plural = "Tarjetas Internacionales"

    def __str__(self):
        return f"{self.medio_pago.nombre} - ****{self.ultimos_digitos}"


class Billetera(models.Model):
    medio_pago = models.OneToOneField(
        "MedioPago",
        on_delete=models.CASCADE,
        related_name="billetera",
        verbose_name="Medio de Pago"
    )
    numero_celular = models.CharField(max_length=20, verbose_name="Número de Celular")

    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "telefono"},
        verbose_name="Proveedor",
        null=False
    )

    moneda = models.ForeignKey("Currency", on_delete=models.PROTECT, verbose_name="Moneda", editable=False, default=1)

    class Meta:
        db_table = "billeteras"
        verbose_name = "Billetera"
        verbose_name_plural = "Billeteras"

    def __str__(self):
        return f"{self.medio_pago.nombre} - {self.entidad.nombre}"


class CuentaBancaria(models.Model):
    medio_pago = models.OneToOneField(
        "MedioPago",
        on_delete=models.CASCADE,
        related_name="cuenta_bancaria",
        verbose_name="Medio de Pago"
    )
    numero_cuenta = models.CharField(max_length=50, verbose_name="Número de Cuenta")
    alias_cbu = models.CharField(max_length=50, verbose_name="Alias/CBU")

    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "banco"},
        verbose_name="Banco",
        null=False
    )

    moneda = models.ForeignKey("Currency", on_delete=models.PROTECT, verbose_name="Moneda", editable=False, default=1)

    class Meta:
        db_table = "cuentas_bancarias"
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"

    def __str__(self):
        return f"{self.medio_pago.nombre} - {self.entidad.nombre}"

class CuentaBancariaNegocio(models.Model):
    """
    Representa una cuenta bancaria asociada a un negocio.
    Tiene los mismos atributos que la cuenta bancaria tradicional,
    pero se mantiene separada para manejar pagos empresariales.
    """
    numero_cuenta: str = models.CharField(
        max_length=50,
        verbose_name="Número de Cuenta"
    )
    alias_cbu: str = models.CharField(
        max_length=50,
        verbose_name="Alias/CBU"
    )
    entidad: Entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "banco"},
        verbose_name="Banco",
        null=False
    )
    moneda: Currency = models.ForeignKey(
        "Currency",
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1
    )

    class Meta:
        db_table = "cuentas_bancarias_negocios"
        verbose_name = "Cuenta Bancaria de Negocio"
        verbose_name_plural = "Cuentas Bancarias de Negocios"

    def __str__(self) -> str:
        return f"{self.entidad.nombre} ({self.alias_cbu}) {self.numero_cuenta}"

# Administracion de metodo de pago global (para admin)

class TipoPago(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    comision = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Tipo de Pago"
        verbose_name_plural = "Tipos de Pago"

    def __str__(self):
        return self.nombre


# -------------------------------------
# Modelo de métodos de cobro genérico
# -------------------------------------
class MedioCobro(models.Model):
    # Opciones predefinidas para los métodos de cobro
    TIPO_CHOICES = [
        ('tauser', 'Tauser'),
        ('billetera', 'Billetera Electrónica'),
        ('cuenta_bancaria', 'Cuenta Bancaria'),
    ]
    
    # Relación con el cliente
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="medios_cobro",
        verbose_name="Cliente"
    )
    
    # Tipo de método de cobro
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Método de Cobro"
    )
    
    # Nombre descriptivo del método de cobro (ej: "Visa Principal", "Mercado Pago")
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre del Método de Cobro"
    )
    
    # Estado del método de cobro (activo/inactivo)
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    
    # Fecha de creación
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    # Fecha de última actualización
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )
    
    tipo_cobro = models.ForeignKey(
        "TipoCobro",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tipo de Cobro Global",
        help_text="Configuración global de activación y comisión",
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        default=1
    )
    
    class Meta:
        db_table = "medios_cobro"
        verbose_name = "Método de Cobro"
        verbose_name_plural = "Métodos de Cobro"
        ordering = ["cliente__nombre", "tipo", "nombre"]
        unique_together = ("cliente", "tipo", "nombre")
    
    def __str__(self):
        return f"{self.cliente.nombre} - {self.get_tipo_display()} - {self.nombre}"


# -------------------------------------
# Administración de métodos de cobro
# -------------------------------------

"""class TarjetaCobro(models.Model):
    medio_cobro = models.OneToOneField(
        "MedioCobro",
        on_delete=models.CASCADE,
        related_name="tarjeta_cobro",
        verbose_name="Método de Cobro"
    )
    numero_tokenizado = models.CharField(max_length=50, verbose_name="Número Tokenizado")
    fecha_vencimiento = models.DateField(verbose_name="Fecha de Vencimiento")
    ultimos_digitos = models.CharField(max_length=4, verbose_name="Últimos 4 Dígitos")

    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "banco"},
        verbose_name="Banco Emisor",
        null=False
    )

    moneda = models.ForeignKey("Currency", on_delete=models.PROTECT, verbose_name="Moneda", editable=False, default=1)

    class Meta:
        db_table = "tarjetas_cobro"
        verbose_name = "Tarjeta de Cobro"
        verbose_name_plural = "Tarjetas de Cobro"

    def __str__(self):
        return f"{self.medio_cobro.nombre} - ****{self.ultimos_digitos} ({self.entidad.nombre})"
"""

class BilleteraCobro(models.Model):
    medio_cobro = models.OneToOneField(
        "MedioCobro",
        on_delete=models.CASCADE,
        related_name="billetera_cobro",
        verbose_name="Método de Cobro"
    )
    numero_celular = models.CharField(max_length=20, verbose_name="Número de Celular")

    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "telefono"},
        verbose_name="Proveedor",
        null=False
    )

    moneda = models.ForeignKey("Currency", on_delete=models.PROTECT, verbose_name="Moneda", editable=False, default=1)

    class Meta:
        db_table = "billeteras_cobro"
        verbose_name = "Billetera de Cobro"
        verbose_name_plural = "Billeteras de Cobro"

    def __str__(self):
        return f"{self.medio_cobro.nombre} - {self.entidad.nombre}"


class CuentaBancariaCobro(models.Model):
    medio_cobro = models.OneToOneField(
        "MedioCobro",
        on_delete=models.CASCADE,
        related_name="cuenta_bancaria_cobro",
        verbose_name="Método de Cobro"
    )
    numero_cuenta = models.CharField(max_length=50, verbose_name="Número de Cuenta")
    alias_cbu = models.CharField(max_length=50, verbose_name="Alias/CBU")

    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.PROTECT,
        limit_choices_to={"tipo": "banco"},
        verbose_name="Banco",
        null=False
    )

    moneda = models.ForeignKey("Currency", on_delete=models.PROTECT, verbose_name="Moneda", editable=False, default=1)

    class Meta:
        db_table = "cuentas_bancarias_cobro"
        verbose_name = "Cuenta Bancaria de Cobro"
        verbose_name_plural = "Cuentas Bancarias de Cobro"

    def __str__(self):
        return f"{self.medio_cobro.nombre} - {self.entidad.nombre}"



# Administración de método de cobro global (para admin)

class TipoCobro(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    comision = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        verbose_name = "Tipo de Cobro"
        verbose_name_plural = "Tipos de Cobro"

    def __str__(self):
        return self.nombre

# ------------------------
# Modelos para el tauser
# ------------------------

# Modelo Tauser que representa un medio de pago/cobro específico de la casa
class Tauser(models.Model):
    tipo = "Tauser"

    # Heredamos campos básicos de pago/cobro
    tipo_cobro = models.ForeignKey(
        "TipoCobro",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tipo de Cobro Global",
        help_text="Configuración global de activación y comisión"
    )

    tipo_pago = models.ForeignKey(
        "TipoPago",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tipo de Pago Global",
        help_text="Configuración global de activación y comisión"
    )

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    ubicacion = models.CharField(max_length=200, null=True, blank=True, verbose_name="Ubicación")  # Campo ubicación
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de Actualización")

    class Meta:
        db_table = "tauser"
        verbose_name = "Tauser"
        verbose_name_plural = "Tausers"

    def __str__(self):
        return f"{self.nombre} ({self.tipo})"

# Tabla intermedia entre Tauser y Currency
"""
class TauserCurrency(models.Model):
    tauser = models.ForeignKey(Tauser, on_delete=models.CASCADE, related_name="monedas")
    currency = models.ForeignKey("Currency", on_delete=models.PROTECT, related_name="tausers")
    stock = models.DecimalField(max_digits=20, decimal_places=2, default=0.0, verbose_name="Stock disponible")

    class Meta:
        db_table = "tauser_currency"
        verbose_name = "Stock Tauser por Moneda"
        verbose_name_plural = "Stocks Tauser por Moneda"
        unique_together = ("tauser", "currency")

    def __str__(self):
        return f"{self.tauser.nombre} - {self.currency.code}: {self.stock}"
"""

# ------------------------------------------------------
# Modelo Transaccion para el registro de la compraventa
# ------------------------------------------------------
class Transaccion(models.Model):
    class Tipo(models.TextChoices):
        COMPRA = "COMPRA", "Compra"
        VENTA = "VENTA", "Venta"

    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADA = "PAGADA", "Pagada por el cliente"
        COMPLETA = "COMPLETA", "Transacción finalizada"
        AC_FALLIDA = "ac_fallida", "Error al acreditar"
        CANCELADA = "CANCELADA", "Cancelada"
        ANULADA = "ANULADA", "Anulada"

    cliente = models.ForeignKey(
        "Cliente",
        on_delete=models.CASCADE,
        related_name="transacciones"
    )
    usuario = models.ForeignKey(
        "webapp.CustomUser",  # ajusta al nombre real de tu User
        on_delete=models.CASCADE,
        related_name="transacciones"
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    estado = models.CharField(
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    moneda_origen = models.ForeignKey(
        "Currency",
        on_delete=models.PROTECT,
        related_name="transacciones_origen"
    )
    moneda_destino = models.ForeignKey(
        "Currency",
        on_delete=models.PROTECT,
        related_name="transacciones_destino"
    )
    
    tasa_cambio = models.DecimalField(max_digits=16, decimal_places=8)
    monto_origen = models.DecimalField(max_digits=20, decimal_places=8)
    monto_destino = models.DecimalField(max_digits=20, decimal_places=8)

    # Generic Foreign Key para medio de pago
    medio_pago_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="transacciones_pago"
    )
    medio_pago_id = models.PositiveIntegerField()
    medio_pago = GenericForeignKey("medio_pago_type", "medio_pago_id")

    medio_cobro_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="transacciones_cobro"
    )
    medio_cobro_id = models.PositiveIntegerField()
    medio_cobro = GenericForeignKey("medio_cobro_type", "medio_cobro_id")

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="ID de PaymentIntent en Stripe"
    )

    id_transferencia = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="ID de transferencia"
    )

    factura_asociada = models.ForeignKey(
        "Factura",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transacciones"
    )

    # ----------------------------------------------------------------------
    # 🔹 Control automático de fechas según estado
    # ----------------------------------------------------------------------
    def save(self, *args, **kwargs):
        """
        Controla automáticamente las fechas de pago y actualización.
        """
        estado_anterior = None
        if self.pk:
            estado_anterior = (
                Transaccion.objects.filter(pk=self.pk)
                .values_list("estado", flat=True)
                .first()
            )

        # 🔸 1. Si el estado es PAGADA y aún no tiene fecha de pago → se setea ahora
        if self.estado == self.Estado.PAGADA and not self.fecha_pago:
            self.fecha_pago = timezone.now()

        # 🔸 2. Si el estado cambió (a COMPLETA, CANCELADA, etc.) → se actualiza la fecha de actualización
        if not self.pk or self.estado != estado_anterior:
            self.fecha_actualizacion = timezone.now()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} {self.monto_origen} {self.moneda_origen} → {self.moneda_destino} ({self.estado})"
        
    @property
    def tauser_display(self):
        if isinstance(self.medio_pago, Tauser):
            return f"{self.medio_pago.nombre} ({self.medio_pago.ubicacion})"
        elif isinstance(self.medio_cobro, Tauser):
            return f"{self.medio_cobro.nombre} ({self.medio_cobro.ubicacion})"
        return ""

    
# --------------------------------------------
# Modelos para facturación y notas de crédito
# --------------------------------------------

class Factura(models.Model):
    ESTADOS = [
        ("emitida", "Emitida"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
    ]

    timbrado = models.IntegerField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cliente = models.ForeignKey("Cliente", on_delete=models.CASCADE)
    fechaEmision = models.DateField(default=timezone.now)
    detalleFactura = models.ForeignKey("DetalleFactura", on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="emitida")
    xml_file = models.FileField(upload_to="facturas/xml/", blank=True, null=True)
    pdf_file = models.FileField(upload_to="facturas/pdf/", blank=True, null=True)

    def __str__(self):
        return f"Factura {self.id} - Cliente {self.cliente} ({self.estado})"

class DetalleFactura(models.Model):
    transaccion = models.ForeignKey("Transaccion", on_delete=models.CASCADE)
    
    # Campos para GenericForeignKey
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    medioPago = GenericForeignKey("content_type", "object_id")

    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return f"Detalle {self.id} - {self.descripcion}"
    

# -------------------------------------
# Modelo para definir limites de intercambio por dia y mes
# -------------------------------------

class LimiteIntercambioLog(models.Model):
    transaccion = models.OneToOneField(
        Transaccion,
        on_delete=models.CASCADE,
        related_name="limite_log"
    )
    monto_descontado = models.DecimalField(max_digits=23, decimal_places=8, default=Decimal('0'))
    timestamp = models.DateTimeField(auto_now_add=True)

class LimiteIntercambioConfig(models.Model):
    """
    Config de límites por CATEGORÍA + MONEDA.
    SOLO guarda los topes (máximos).
    """
    categoria = models.ForeignKey(
        Categoria, on_delete=models.CASCADE,
        related_name="limites_config", verbose_name="Categoría"
    )
    moneda = models.ForeignKey(
        Currency, on_delete=models.CASCADE,
        related_name="limites_config_por_moneda", verbose_name="Moneda"
    )

    limite_dia_max = models.DecimalField(
        max_digits=23, decimal_places=8, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))], verbose_name="Límite Diario (Máx.)"
    )
    limite_mes_max = models.DecimalField(
        max_digits=23, decimal_places=8, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))], verbose_name="Límite Mensual (Máx.)"
    )

    class Meta:
        verbose_name = "Config. Límite de Intercambio (Categoría)"
        verbose_name_plural = "Config. Límites de Intercambio (Categoría)"
        constraints = [
            models.UniqueConstraint(
                fields=["categoria", "moneda"],
                name="uniq_limite_config_categoria_moneda"
            )
        ]
        ordering = ["categoria__id", "moneda__code"]

    def _factor(self) -> Decimal:
        dec = int(self.moneda.decimales_cotizacion or 0)
        return Decimal("1").scaleb(-dec)

    def clean(self):
        factor = self._factor()
        for f in ["limite_dia_max", "limite_mes_max"]:
            v = getattr(self, f)
            if v is not None and Decimal(v).quantize(factor, rounding=ROUND_DOWN) != Decimal(v):
                raise ValidationError({f: f"Excede decimales permitidos para {self.moneda.code}."})

    def save(self, *args, **kwargs):
        factor = self._factor()
        self.limite_dia_max = Decimal(self.limite_dia_max).quantize(factor, rounding=ROUND_DOWN)
        self.limite_mes_max = Decimal(self.limite_mes_max).quantize(factor, rounding=ROUND_DOWN)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.categoria} / {self.moneda.code} (MAX)"


class LimiteIntercambioCliente(models.Model):
    """
    Saldo disponible por CLIENTE,
    vinculado a una configuración específica (Categoría + Moneda).
    SOLO guarda valores ACTUALES (saldo).
    """
    config = models.ForeignKey(
        LimiteIntercambioConfig,
        on_delete=models.CASCADE,
        related_name="saldos_por_cliente",
        verbose_name="Configuración de límite (Categoría + Moneda)"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="limites_cliente",
        verbose_name="Cliente"
    )

    limite_dia_actual = models.DecimalField(
        max_digits=23, decimal_places=8, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Límite Diario (Actual)"
    )
    limite_mes_actual = models.DecimalField(
        max_digits=23, decimal_places=8, default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Límite Mensual (Actual)"
    )

    class Meta:
        verbose_name = "Límite de Intercambio (Cliente)"
        verbose_name_plural = "Límites de Intercambio (Cliente)"
        constraints = [
            models.UniqueConstraint(
                fields=["cliente", "config"],
                name="uniq_limite_cliente_config"
            )
        ]
        ordering = ["cliente__id"]

    # 🔧 Normalizador de decimales, basado en la moneda real
    def _quant(self, value: Decimal) -> Decimal:
        factor = self.config._factor()  # Usa moneda desde la config
        return Decimal(value).quantize(factor, rounding=ROUND_DOWN)

    # 💰 Descontar cupo (solo se invoca si ya validamos antes)
    def descontar(self, monto: Decimal):
        monto = self._quant(monto)
        if monto <= 0:
            raise ValidationError("El monto debe ser positivo.")

        if monto > self.limite_dia_actual:
            raise ValidationError(f"Supera el límite DIARIO ({self.limite_dia_actual}).")

        if monto > self.limite_mes_actual:
            raise ValidationError(f"Supera el límite MENSUAL ({self.limite_mes_actual}).")

        self.limite_dia_actual = self._quant(self.limite_dia_actual - monto)
        self.limite_mes_actual = self._quant(self.limite_mes_actual - monto)
        self.save(update_fields=["limite_dia_actual", "limite_mes_actual"])

    # 🔄 Reset duros (Celery)
    def reset_diario(self):
        self.limite_dia_actual = self._quant(self.config.limite_dia_max)
        self.save(update_fields=["limite_dia_actual"])

    def reset_mensual(self):
        self.limite_mes_actual = self._quant(self.config.limite_mes_max)
        self.save(update_fields=["limite_mes_actual"])

    def __str__(self):
        return f"{self.cliente} / {self.config.moneda.code} (ACTUAL)"


# --------------------------------------------
# Modelos para Schedule
# --------------------------------------------

class ExpiracionTransaccionConfig(models.Model):
    MEDIOS = [
        ("cuenta_bancaria_negocio", "Transferencia"),
        ("tauser", "Tauser"),
    ]

    medio = models.CharField(max_length=40, choices=MEDIOS, unique=True)
    minutos_expiracion = models.PositiveIntegerField(default=2)

    def __str__(self):
        return f"{self.get_medio_display()} → {self.minutos_expiracion} min"


class LimiteIntercambioScheduleConfig(models.Model):
    """
    Configuración GLOBAL para el reseteo de límites de intercambio.

    - frequency:
        - 'daily'   → resetea todos los días a (hour:minute)
        - 'monthly' → resetea el día `month_day` de cada mes a (hour:minute)
    - hour/minute: hora exacta local del servidor/APP en la que se ejecutará el reseteo.
    - month_day: solo aplicable cuando frequency='monthly'.
    - is_active: permite desactivar el reseteo sin borrar la config.

    Este modelo es SINGLETON: debe existir a lo sumo 1 fila.
    Se fuerza con UniqueConstraint(true) usando una clave constante.
    """

    FREQUENCIES = (
        ("daily", "Diario"),
        ("monthly", "Mensual"),
    )

    frequency = models.CharField(max_length=20, choices=FREQUENCIES, unique=True)  # ✅ solo 1 por tipo
    hour = models.PositiveSmallIntegerField(default=0)    # 0–23
    minute = models.PositiveSmallIntegerField(default=0)  # 0–59

    month_day = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Día del mes (1–31). Solo si frequency='monthly'."
    )

    is_active = models.BooleanField(default=True)

    # para evitar reinicios duplicados
    last_executed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Temporizador global de reseteo de límites"
        verbose_name_plural = "Temporizador global de reseteo de límites"

    def __str__(self) -> str:
        base = f"{self.get_frequency_display()} @ {self.hour:02d}:{self.minute:02d}"
        if self.frequency == "monthly" and self.month_day:
            base = f"Cada mes el día {self.month_day} @ {self.hour:02d}:{self.minute:02d}"
        return f"(GLOBAL) {base} | {'Activo' if self.is_active else 'Inactivo'}"

    # ---- Helpers de dominio ----
    def requires_month_day(self) -> bool:
        """Indica si el campo month_day es requerido por la frecuencia actual."""
        return self.frequency == "monthly"

    @classmethod
    def get_by_frequency(cls, freq: str) -> "LimiteIntercambioScheduleConfig":
        """Obtiene (o crea) la config específica para daily o monthly."""
        obj, _ = cls.objects.get_or_create(
            frequency=freq,
            defaults=dict(hour=0, minute=0, is_active=True)
        )
        return obj

class EmailScheduleConfig(models.Model):
    """
    Configuración para la frecuencia de envío de correos con tasas de cambio.
    """
    frequency = models.CharField(
        max_length=20,
        choices=[
            ("daily", "Diario"),
            ("weekly", "Semanal"),
            ("custom", "Personalizado"),
        ],
        default="daily"
    )
    hour = models.IntegerField(default=8)
    minute = models.IntegerField(default=0)
    interval_minutes = models.IntegerField(null=True, blank=True)

    # ✅ Nuevo campo para 'weekly'
    weekday = models.CharField(
        max_length=10,
        choices=[
            ("monday", "Lunes"),
            ("tuesday", "Martes"),
            ("wednesday", "Miércoles"),
            ("thursday", "Jueves"),
            ("friday", "Viernes"),
            ("saturday", "Sábado"),
            ("sunday", "Domingo"),
        ],
        null=True,
        blank=True,
    )

    def __str__(self):
        desc = f"Envío {self.frequency} a las {self.hour:02d}:{self.minute:02d}"
        if self.frequency == "weekly" and self.weekday:
            desc += f" ({self.get_weekday_display()})"
        return desc


class MFACode(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    used = models.BooleanField(default=False)

    def is_valid(self):
        """Verifica que el código no esté expirado (5 minutos) ni usado."""
        return not self.used and (timezone.now() - self.created_at).total_seconds() < 300

    @staticmethod
    def generate_for_user(user):
        """Genera y envía un nuevo código MFA al correo del usuario usando templates HTML y TXT."""
        code = str(secrets.randbelow(1000000)).zfill(6)
        mfa = MFACode.objects.create(user=user, code=code)

        # Context for the templates
        context = {
            "user": user,
            "code": code,
            "project_name": "Global Exchange"  # or use settings.PROJECT_NAME
        }

        # Render plain text and HTML versions
        text_content = render_to_string("emails/mfa_transaccion.txt", context)
        html_content = render_to_string("emails/mfa_transaccion.html", context)

        # Create email
        subject = "Tu código de verificación (MFA)"
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return mfa


class DocSequence(models.Model):
    est = models.CharField(max_length=3, default="001")
    pun = models.CharField(max_length=3, default="003")
    min_num = models.IntegerField(default=151)
    max_num = models.IntegerField(default=200)
    current_num = models.IntegerField(default=150)
    active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("est", "pun")

    def next_numdoc(self) -> str:
        # ⚠️ este atomic hace que el select_for_update ocurra DENTRO de una transacción
        with transaction.atomic():
            # bloqueamos la fila de esta secuencia
            seq = DocSequence.objects.select_for_update().get(pk=self.pk)
            if seq.current_num >= seq.max_num:
                raise RuntimeError("Rango de documentos agotado (151–200).")
            seq.current_num += 1
            seq.save(update_fields=["current_num"])
            return str(seq.current_num).zfill(7)