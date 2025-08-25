from django.db import models
from django.conf import settings

# --------------------------------------------------------------
# Modelo de la tabla cliente para migración en la tabla de datos
# --------------------------------------------------------------
class Cliente(models.Model):
    tipoCliente = models.CharField(
        max_length=50,
        choices=[
            ('persona_fisica', 'Persona Física'),
            ('persona_juridica', 'Persona Jurídica'),
        ],
        verbose_name="Tipo de Cliente"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre")
    razonSocial = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name="Razón Social"
    )
    documento = models.CharField(max_length=20, verbose_name="Documento")
    ruc = models.CharField(max_length=20, null=True, blank=True, verbose_name="RUC")
    correo = models.EmailField(max_length=150, unique=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=30, verbose_name="Teléfono")
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('mino', 'Minorista'),
            ('corp', 'Corporativo'),
            ('vip', 'VIP'),
        ],
        default='mino',
        verbose_name="Categoría"
    )
    estado = models.BooleanField(default=True, verbose_name="Activo")
    fechaRegistro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    def __str__(self):
        return f"{self.nombre} ({self.tipoCliente})"

    class Meta:
        db_table = "clientes"
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["-fechaRegistro"]

# -----------------------------------------------------------------
# Modelo de la tabla intermedia que relaciona usuarios con clientes
# -----------------------------------------------------------------
class ClienteUsuario(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Asignación")

    def __str__(self):
        return f"Cliente: {self.cliente.nombre} - Usuario: {self.usuario.username}"

    class Meta:
        db_table = "cliente_usuario"
        unique_together = ("cliente", "usuario")  # Evita duplicar relaciones
        verbose_name = "Cliente-Usuario"
        verbose_name_plural = "Clientes-Usuarios"
