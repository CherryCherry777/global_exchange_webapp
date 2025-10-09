# signals.py
from django.conf import settings
from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Billetera, Entidad, Role, MedioPago, TipoPago
from django.contrib.auth.models import Group, Permission
from django.apps import apps


User = get_user_model()


# Función para borrar sesiones solo en desarrollo
def clear_sessions(sender, **kwargs):
    if settings.DEBUG:
        print("Borrando todas las sesiones activas (solo dev)...")
        # importar aquí dentro, no al nivel de módulo
        from django.contrib.sessions.models import Session
        Session.objects.all().delete()


@receiver(post_migrate)
def create_default_roles_and_admin(sender, **kwargs):
    if sender.name == "webapp":
        for role_name in ["Usuario", "Empleado", "Administrador", "Analista"]:
            group, _ = Group.objects.get_or_create(name=role_name)
            Role.objects.get_or_create(group=group)

        username = "superadmin2"
        password = "password12345"
        email = "admin2@example.com"

        if not User.objects.filter(username=username).exists():
            admin_group = Group.objects.get(name="Administrador")
            user = User.objects.create_user(username=username, password=password, email=email)
            user.groups.add(admin_group)
            user.is_active = True
            user.save()
            print(f"Usuario admin por defecto '{username}' creado con contraseña '{password}'")
        else:
            print(f"Usuario admin '{username}' ya existe")


@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    if created:
        try:
            default_group = Group.objects.get(name="Usuario")
            Role.objects.get_or_create(group=default_group)
            instance.groups.add(default_group)
        except Group.DoesNotExist:
            pass

@receiver(post_migrate)
def assign_all_permissions_to_admin(sender, **kwargs):
    if sender.name == "webapp":
        try:
            admin_group = Group.objects.get(name="Administrador")
        except Group.DoesNotExist:
            return

        # Asignar todos los permisos disponibles al grupo Administrador
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)

@receiver(post_migrate)
def create_default_payment_types(sender, **kwargs):
    # Asegurarse de que solo se ejecute para nuestra app
    if sender.name != "webapp":
        return

    TipoPago = apps.get_model("webapp", "TipoPago")
    defaults = {"activo": True, "comision": 0.0}
    
    # Lista de tipos de pago fijos
    tipos = ["Billetera", """"Cuenta Bancaria",""" "Tauser", "Tarjeta"]
    
    for nombre in tipos:
        TipoPago.objects.get_or_create(nombre=nombre, defaults=defaults)

@receiver(post_save, sender=MedioPago)
def asignar_tipo_pago(sender, instance, created, **kwargs):
    if created and not instance.tipo_pago:
        tipo_pago, _ = TipoPago.objects.get_or_create(nombre=instance.tipo.capitalize())
        instance.tipo_pago = tipo_pago
        instance.save()

@receiver(post_migrate)
def crear_limites_intercambio(sender, **kwargs):
    # Asegurarnos de que los modelos ya estén cargados
    Currency = apps.get_model('webapp', 'Currency')
    LimiteIntercambio = apps.get_model('webapp', 'LimiteIntercambio')

    # Evitamos ejecutarlo para apps que no sean la tuya
    if sender.label != 'webapp':
        return

    # Iterar sobre todas las monedas y categorías
    for moneda in Currency.objects.all():
        
        # Crear el límite si no existe
        LimiteIntercambio.objects.get_or_create(
            moneda=moneda,
            defaults={
                'limite_dia': 1000,     # valor por defecto mínimo
                'limite_mes': 1000   # valor por defecto máximo
            }
        )

@receiver(post_save, sender='webapp.Currency')
def crear_limites_por_moneda(sender, instance, created, **kwargs):
    """
    Crea automáticamente registros de LimiteIntercambio para todas las categorías
    cuando se crea una nueva moneda.
    """
    if not created:
        return  # Solo al crear la moneda

    LimiteIntercambio = apps.get_model('webapp', 'LimiteIntercambio')
    LimiteIntercambio.objects.create(
        moneda=instance,
        limite_dia=0,
        limite_mes=0
    )


@receiver(post_save, sender=TipoPago)
def sync_medios_pago(sender, instance, **kwargs):
    # Sincroniza el estado de todos los MedioPago vinculados
    MedioPago.objects.filter(tipo_pago=instance).update(activo=instance.activo)


# signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Currency

@receiver(post_migrate)
def create_default_currency(sender, **kwargs):
    # Evitar que se ejecute para apps que no sean la tuya
    if sender.name != "webapp":
        return

    if Currency.objects.count() == 0:
        Currency.objects.create(
            code="PYG",
            name="Guaraní Paraguayo",
            symbol="G",
            base_price=1.0,
            comision_venta=1.0,
            comision_compra=1.0,
            decimales_cotizacion=2,
            decimales_monto=0,
            is_active=True
        )
        print("Se creó la moneda por defecto: Guaraní Paraguayo (PYG)")

@receiver(post_migrate)
def create_default_cobro_types(sender, **kwargs):
    # Asegurarse de que solo se ejecute para nuestra app
    if sender.name != "webapp":
        return

    TipoCobro = apps.get_model("webapp", "TipoCobro")
    defaults = {"activo": True, "comision": 0.0}
    
    # Lista de tipos de pago fijos
    tipos = ["Billetera", "Cuenta Bancaria", "Tauser"]
    
    for nombre in tipos:
        TipoCobro.objects.get_or_create(nombre=nombre, defaults=defaults)


@receiver(post_migrate)
def crear_entidades_genericas(sender, **kwargs):
    """
#     Crea entidades genéricas si no existen:
#     - Bancos
#     - Compañías de billetera/telefonía
#     """
    if sender.name != 'webapp':
        return

    bancos = [
        "Banco Nacional de Paraguay",
        "Banco Regional",
        "Banco Continental"
    ]

    billeteras = [
        "Bancard Wallet",
        "Tigo Money",
        "Personal Wallet"
    ]

    for nombre in bancos:
        Entidad.objects.get_or_create(nombre=nombre, defaults={"tipo": "banco", "activo": True})

    for nombre in billeteras:
        Entidad.objects.get_or_create(nombre=nombre, defaults={"tipo": "telefono", "activo": True})
