from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.conf import settings

#Las clases van aqui
#Los usuarios heredan AbstractUser
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

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
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Tipo de cambio")
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

    # Categoría del cliente, definida mediante opciones
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('mino', 'Minorista'),   # Cliente minorista
            ('corp', 'Corporativo'), # Cliente corporativo
            ('vip', 'VIP'),          # Cliente VIP
        ],
        default='mino',             # Valor por defecto: minorista
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