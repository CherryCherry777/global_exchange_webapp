from django.contrib.auth.models import AbstractUser, Group
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_DOWN

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

    class Meta:
        permissions = [
            ("access_admin_panel", "Can access admin panel")
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


# -------------------------------------
# Modelo de medios de pago genérico
# -------------------------------------
class MedioPago(models.Model):
    # Opciones predefinidas para los medios de pago
    TIPO_CHOICES = [
        ('tarjeta', 'Tarjeta de Débito/Crédito'),
        ('billetera', 'Billetera Electrónica'),
        ('cuenta_bancaria', 'Cuenta Bancaria'),
        ('cheque', 'Cheque'),
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
        max_length=20,
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
    
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Medio de Pago"
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
        #editable=False,
        default=1 #ID de la moneda por defecto
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

class Tarjeta(models.Model):
    # Relación con el medio de pago genérico
    medio_pago = models.OneToOneField(
        MedioPago,
        on_delete=models.CASCADE,
        related_name="tarjeta",
        verbose_name="Medio de Pago"
    )
    
    # Número de tarjeta tokenizado (por seguridad)
    numero_tokenizado = models.CharField(
        max_length=50,
        verbose_name="Número Tokenizado",
        help_text="Número de tarjeta encriptado/tokenizado"
    )
    
    # Banco emisor
    banco = models.CharField(
        max_length=100,
        verbose_name="Banco Emisor"
    )
    
    # Fecha de vencimiento
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento"
    )
    
    # Últimos 4 dígitos para identificación (sin tokenizar)
    ultimos_digitos = models.CharField(
        max_length=4,
        verbose_name="Últimos 4 Dígitos"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1 #ID de la moneda por defecto
    )

    #activo = models.BooleanField(default=True, verbose_name="Activo")
    #comision = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Comisión (%)")
    
    class Meta:
        db_table = "tarjetas"
        verbose_name = "Tarjeta"
        verbose_name_plural = "Tarjetas"
    
    def __str__(self):
        return f"{self.medio_pago.nombre} - ****{self.ultimos_digitos}"


class Billetera(models.Model):
    # Relación con el medio de pago genérico
    medio_pago = models.OneToOneField(
        MedioPago,
        on_delete=models.CASCADE,
        related_name="billetera",
        verbose_name="Medio de Pago"
    )
    
    # Número de celular asociado
    numero_celular = models.CharField(
        max_length=20,
        verbose_name="Número de Celular"
    )
    
    # Proveedor de la billetera (Mercado Pago, PayPal, etc.)
    proveedor = models.CharField(
        max_length=100,
        verbose_name="Proveedor"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1 #ID de la moneda por defecto
    )

    
    class Meta:
        db_table = "billeteras"
        verbose_name = "Billetera"
        verbose_name_plural = "Billeteras"

    #activo = models.BooleanField(default=True, verbose_name="Activo")
    #comision = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Comisión (%)")
    
    def __str__(self):
        return f"{self.medio_pago.nombre} - {self.proveedor}"


class CuentaBancaria(models.Model):
    # Relación con el medio de pago genérico
    medio_pago = models.OneToOneField(
        MedioPago,
        on_delete=models.CASCADE,
        related_name="cuenta_bancaria",
        verbose_name="Medio de Pago"
    )
    
    # Número de cuenta
    numero_cuenta = models.CharField(
        max_length=50,
        verbose_name="Número de Cuenta"
    )
    
    # Banco
    banco = models.CharField(
        max_length=100,
        verbose_name="Banco"
    )
    
    # Alias o CBU
    alias_cbu = models.CharField(
        max_length=50,
        verbose_name="Alias/CBU"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1 #ID de la moneda por defecto
    )

    #activo = models.BooleanField(default=True, verbose_name="Activo")
    #comision = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Comisión (%)")
    
    class Meta:
        db_table = "cuentas_bancarias"
        verbose_name = "Cuenta Bancaria"
        verbose_name_plural = "Cuentas Bancarias"
    
    def __str__(self):
        return f"{self.medio_pago.nombre} - {self.banco}"


class Cheque(models.Model):
    # Relación con el medio de pago genérico
    medio_pago = models.OneToOneField(
        MedioPago,
        on_delete=models.CASCADE,
        related_name="cheque",
        verbose_name="Medio de Pago"
    )
    
    # Número de cheque
    numero_cheque = models.CharField(
        max_length=50,
        verbose_name="Número de Cheque"
    )
    
    # Banco emisor
    banco_emisor = models.CharField(
        max_length=100,
        verbose_name="Banco Emisor"
    )
    
    # Fecha de vencimiento
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento"
    )
    
    # Monto del cheque
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Monto"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1 #ID de la moneda por defecto
    )

    #activo = models.BooleanField(default=True, verbose_name="Activo")
    #comision = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Comisión (%)")
    
    class Meta:
        db_table = "cheques"
        verbose_name = "Cheque"
        verbose_name_plural = "Cheques"
    
    def __str__(self):
        return f"{self.medio_pago.nombre} - {self.numero_cheque}"


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
# Modelo para definir maximos y minimos en la categoria de clientes
# -------------------------------------

class LimiteIntercambio(models.Model):
    moneda = models.ForeignKey(
        'Currency',
        on_delete=models.CASCADE,
        verbose_name="Moneda",
        related_name="limites_intercambio"
    )
    categoria = models.ForeignKey(
        'Categoria',
        on_delete=models.CASCADE,
        verbose_name="Categoría de Cliente",
        related_name="limites_intercambio"
    )
    monto_min = models.DecimalField(
        max_digits=23,
        decimal_places=8,
        verbose_name="Monto Mínimo",
        error_messages={
            'max_digits': 'El número no puede tener más de 23 dígitos',
            'max_decimal_places': 'El número no puede tener más de 8 decimales'
        }
    )
    monto_max = models.DecimalField(
        max_digits=23,
        decimal_places=8,
        verbose_name="Monto Máximo",
        error_messages={
            'max_digits': 'El número no puede tener más de 23 dígitos',
            'max_decimal_places': 'El número no puede tener más de 8 decimales'
        }
    )

    class Meta:
        unique_together = ('moneda', 'categoria')
        verbose_name = "Límite de Intercambio"
        verbose_name_plural = "Límites de Intercambio"
        ordering = ['moneda__code', 'categoria__nombre']

    def clean(self):
        if not self.moneda:
            return

        max_dec = self.moneda.decimales_cotizacion

        def check_decimals(value, field_name):
            if value is None:
                return
            str_val = str(value)
            if '.' in str_val:
                dec_count = len(str_val.split('.')[1])
                if dec_count > max_dec:
                    raise ValidationError(
                        {field_name: f"El número máximo de decimales permitidos para esta moneda es {max_dec}."}
                    )

        check_decimals(self.monto_min, 'monto_min')
        check_decimals(self.monto_max, 'monto_max')

        if self.monto_min is not None and self.monto_max is not None:
            if self.monto_min > self.monto_max:
                raise ValidationError("El monto mínimo no puede ser mayor al monto máximo.")

    def save(self, *args, **kwargs):
        if self.moneda:
            dec = int(self.moneda.decimales_cotizacion)
            factor = Decimal('1').scaleb(-dec)  # Ej: dec=3 -> 0.001
            if self.monto_min is not None:
                self.monto_min = Decimal(self.monto_min).quantize(factor, rounding=ROUND_DOWN)
            if self.monto_max is not None:
                self.monto_max = Decimal(self.monto_max).quantize(factor, rounding=ROUND_DOWN)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.moneda.code} - {self.categoria.nombre}"
    
# -------------------------------------
# Modelo de métodos de cobro genérico
# -------------------------------------
class MedioCobro(models.Model):
    # Opciones predefinidas para los métodos de cobro
    TIPO_CHOICES = [
        ('tarjeta', 'Tarjeta de Débito/Crédito'),
        ('billetera', 'Billetera Electrónica'),
        ('cuenta_bancaria', 'Cuenta Bancaria'),
        ('cheque', 'Cheque'),
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
        "TipoPago",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Tipo de Cobro Global",
        help_text="Configuración global de activación y comisión"
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
# Modelos específicos por tipo de método de cobro
# -------------------------------------

class TarjetaCobro(models.Model):
    medio_cobro = models.OneToOneField(
        MedioCobro,
        on_delete=models.CASCADE,
        related_name="tarjeta_cobro",
        verbose_name="Método de Cobro"
    )
    
    numero_tokenizado = models.CharField(
        max_length=50,
        verbose_name="Número Tokenizado",
        help_text="Número de tarjeta encriptado/tokenizado"
    )
    
    banco = models.CharField(
        max_length=100,
        verbose_name="Banco Emisor"
    )
    
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento"
    )
    
    ultimos_digitos = models.CharField(
        max_length=4,
        verbose_name="Últimos 4 Dígitos"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1
    )
    
    class Meta:
        db_table = "tarjetas_cobro"
        verbose_name = "Tarjeta de Cobro"
        verbose_name_plural = "Tarjetas de Cobro"
    
    def __str__(self):
        return f"{self.medio_cobro.nombre} - ****{self.ultimos_digitos}"


class BilleteraCobro(models.Model):
    medio_cobro = models.OneToOneField(
        MedioCobro,
        on_delete=models.CASCADE,
        related_name="billetera_cobro",
        verbose_name="Método de Cobro"
    )
    
    numero_celular = models.CharField(
        max_length=20,
        verbose_name="Número de Celular"
    )
    
    proveedor = models.CharField(
        max_length=100,
        verbose_name="Proveedor"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1
    )

    class Meta:
        db_table = "billeteras_cobro"
        verbose_name = "Billetera de Cobro"
        verbose_name_plural = "Billeteras de Cobro"
    
    def __str__(self):
        return f"{self.medio_cobro.nombre} - {self.proveedor}"


class CuentaBancariaCobro(models.Model):
    medio_cobro = models.OneToOneField(
        MedioCobro,
        on_delete=models.CASCADE,
        related_name="cuenta_bancaria_cobro",
        verbose_name="Método de Cobro"
    )
    
    numero_cuenta = models.CharField(
        max_length=50,
        verbose_name="Número de Cuenta"
    )
    
    banco = models.CharField(
        max_length=100,
        verbose_name="Banco"
    )
    
    alias_cbu = models.CharField(
        max_length=50,
        verbose_name="Alias/CBU"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1
    )
    
    class Meta:
        db_table = "cuentas_bancarias_cobro"
        verbose_name = "Cuenta Bancaria de Cobro"
        verbose_name_plural = "Cuentas Bancarias de Cobro"
    
    def __str__(self):
        return f"{self.medio_cobro.nombre} - {self.banco}"


class ChequeCobro(models.Model):
    medio_cobro = models.OneToOneField(
        MedioCobro,
        on_delete=models.CASCADE,
        related_name="cheque_cobro",
        verbose_name="Método de Cobro"
    )
    
    numero_cheque = models.CharField(
        max_length=50,
        verbose_name="Número de Cheque"
    )
    
    banco_emisor = models.CharField(
        max_length=100,
        verbose_name="Banco Emisor"
    )
    
    fecha_vencimiento = models.DateField(
        verbose_name="Fecha de Vencimiento"
    )
    
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Monto"
    )

    moneda = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        verbose_name="Moneda",
        editable=False,
        default=1
    )
    
    class Meta:
        db_table = "cheques_cobro"
        verbose_name = "Cheque de Cobro"
        verbose_name_plural = "Cheques de Cobro"
    
    def __str__(self):
        return f"{self.medio_cobro.nombre} - {self.numero_cheque}"


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
