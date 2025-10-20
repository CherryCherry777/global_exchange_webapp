# signals.py
from django.conf import settings
from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Currency, Entidad, LimiteIntercambioConfig, LimiteIntercambioCliente, LimiteIntercambioLog, MedioCobro, Role, MedioPago, TipoCobro, TipoPago, CuentaBancariaNegocio, Transaccion
from django.contrib.auth.models import Group, Permission
from django.apps import apps
from django.db import transaction
from decimal import Decimal
import logging

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

        # Crea tambien un usuario normal listo para usar
        username2 = "usuario1"
        password2 = "password12345"
        email2 = "usuario1@example.com"

        if not User.objects.filter(username=username).exists():
            admin_group = Group.objects.get(name="Administrador")
            user = User.objects.create_user(username=username, password=password, email=email)
            user.groups.add(admin_group)
            user.is_active = True
            user.save()
            print(f"Usuario admin por defecto '{username}' creado con contraseña '{password}'")
        else:
            print(f"Usuario admin '{username}' ya existe")

        if not User.objects.filter(username=username2).exists():
            normal_group = Group.objects.get(name="Usuario")
            user = User.objects.create_user(username=username2, password=password2, email=email2)
            user.groups.add(normal_group)
            user.is_active = True
            user.save()
            print(f"Usuario normal por defecto '{username2}' creado con contraseña '{password2}'")
        else:
            print(f"Usuario normal '{username2}' ya existe")


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
    tipos = ["Billetera", "Cuenta Bancaria", "Tauser", "Tarjeta Nacional", "Tarjeta Internacional"]
    
    for nombre in tipos:
        TipoPago.objects.get_or_create(nombre=nombre, defaults=defaults)

@receiver(post_save, sender=MedioPago)
def asignar_tipo_pago(sender, instance, created, **kwargs):
    if created and not instance.tipo_pago:
        nombre_tipo_pago = " ".join([palabra.capitalize() for palabra in instance.tipo.split("_")])
        tipo_pago, _ = TipoPago.objects.get_or_create(nombre=nombre_tipo_pago)
        instance.tipo_pago = tipo_pago
        instance.save()

# Valores iniciales específicos por moneda (para *_max)
VALORES_POR_MONEDA = {
    "PYG": 1000000,
    "USD": 5000,
    "EUR": 5000,
    "BRL": 20000,
    "ARG": 200000,
}
DEFAULT_NO_LISTADA = 0


@receiver(post_migrate)
def seed_limite_config(sender, **kwargs):
    if sender.label != "webapp":
        return
    Currency = apps.get_model("webapp", "Currency")
    Categoria = apps.get_model("webapp", "Categoria")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")

    for categoria in Categoria.objects.all():
        for moneda in Currency.objects.all():
            valor = VALORES_POR_MONEDA.get(moneda.code, DEFAULT_NO_LISTADA)
            LimiteIntercambioConfig.objects.get_or_create(
                categoria=categoria, moneda=moneda,
                defaults={
                    "limite_dia_max": valor,
                    "limite_mes_max": valor,
                }
            )


@receiver(post_save, sender="webapp.Currency")
def crear_config_al_crear_moneda(sender, instance, created, **kwargs):
    if not created:
        return
    Categoria = apps.get_model("webapp", "Categoria")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")

    valor = VALORES_POR_MONEDA.get(instance.code, DEFAULT_NO_LISTADA)
    for categoria in Categoria.objects.all():
        LimiteIntercambioConfig.objects.get_or_create(
            categoria=categoria, moneda=instance,
            defaults={"limite_dia_max": valor, "limite_mes_max": valor}
        )


@receiver(post_save, sender="webapp.Cliente")
def crear_saldos_cliente(sender, instance, created, **kwargs):
    LimiteIntercambioCliente = apps.get_model("webapp", "LimiteIntercambioCliente")
    LimiteIntercambioConfig = apps.get_model("webapp", "LimiteIntercambioConfig")

    if not instance.categoria_id:
        return

    configs = LimiteIntercambioConfig.objects.filter(categoria=instance.categoria)

    for cfg in configs:
        LimiteIntercambioCliente.objects.get_or_create(
            cliente=instance,
            config=cfg,  # ✅ AQUÍ SE CAMBIA
            defaults={
                "limite_dia_actual": cfg.limite_dia_max,
                "limite_mes_actual": cfg.limite_mes_max,
            }
        )

@receiver(post_save, sender=TipoPago)
def sync_medios_pago(sender, instance, **kwargs):
    # Sincroniza el estado de todos los MedioPago vinculados
    MedioPago.objects.filter(tipo_pago=instance).update(activo=instance.activo)

@receiver(post_save, sender=TipoCobro)
def sync_medios_cobro(sender, instance, **kwargs):
    # Sincroniza el estado de todos los MedioPago vinculados
    MedioCobro.objects.filter(tipo_cobro=instance).update(activo=instance.activo)

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

@receiver(post_migrate)
def asignar_tipos_tauser(sender, **kwargs):
    Tauser = apps.get_model("webapp", "Tauser")
    TipoPago = apps.get_model("webapp", "TipoPago")
    TipoCobro = apps.get_model("webapp", "TipoCobro")

    # Obtener los tipos "Tauser" existentes
    tipo_pago = TipoPago.objects.filter(nombre__icontains="tauser", activo=True).first()
    tipo_cobro = TipoCobro.objects.filter(nombre__icontains="tauser", activo=True).first()

    if not tipo_pago or not tipo_cobro:
        # Si no existen, no hacemos nada
        return

    # Actualizar solo los Tauser que aún no tienen asignado el tipo
    Tauser.objects.filter(tipo_pago__isnull=True).update(tipo_pago=tipo_pago)
    Tauser.objects.filter(tipo_cobro__isnull=True).update(tipo_cobro=tipo_cobro)

@receiver(post_migrate)
def crear_cuenta_bancaria_negocio(sender, **kwargs):
    """
    Crea una cuenta bancaria por defecto para el negocio
    solo si no existe aún, y después de que la moneda PYG esté disponible.
    """
    if sender.name != "webapp":
        return

    # Usamos transaction.on_commit para asegurar que se ejecute
    # después de todas las migraciones y commits
    def crear_si_corresponde():
        try:
            moneda = Currency.objects.filter(code="PYG").first()
            if not moneda:
                print("⚠️ No se creó la cuenta bancaria del negocio porque la moneda PYG aún no existe.")
                return

            banco, _ = Entidad.objects.get_or_create(
                nombre="Banco Continental",
                tipo="banco",
            )

            cuenta_existente = CuentaBancariaNegocio.objects.first()
            if cuenta_existente:
                print("ℹ️ Ya existe una cuenta bancaria del negocio, no se creó otra.")
                return

            CuentaBancariaNegocio.objects.create(
                numero_cuenta="000100000001",
                alias_cbu="CUENTA_NEGOCIO_DEFECTO",
                entidad=banco,
                moneda=moneda,
            )
            print("✅ Se creó la cuenta bancaria del negocio por defecto.")

        except Exception as e:
            print(f"❌ Error al crear cuenta bancaria del negocio: {e}")

    transaction.on_commit(crear_si_corresponde)

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Transaccion)
def actualizar_limite_post_transaccion(sender, instance, **kwargs):
    """
    Lógica bancaria profesional:
    - Si llega a PENDIENTE, PAGADA o COMPLETADA → DESCUENTA SOLO 1 VEZ (reserva cupo)
    - Si luego pasa a CANCELADA o ANULADA → DEVUELVE EXACTAMENTE lo reservado
    - Usa LimiteIntercambioLog como tracking persistente para evitar dobles descuentos
    """

    ESTADOS_DESCUENTAN = [
        Transaccion.Estado.PENDIENTE,
        Transaccion.Estado.PAGADA,
        Transaccion.Estado.COMPLETA,
    ]
    ESTADOS_RESTAURAN = [
        Transaccion.Estado.CANCELADA,
        Transaccion.Estado.ANULADA,
    ]

    # Solo aplica a operaciones de VENTA → origen PYG
    if instance.moneda_origen.code != "PYG":
        return

    try:
        # Traemos el tracking (si ya existía)
        log = LimiteIntercambioLog.objects.filter(transaccion=instance).first()

        # 1) Si es estado que DESCUNTA y aún *NO* se descontó antes → descontar
        if instance.estado in ESTADOS_DESCUENTAN and (not log or log.monto_descontado == 0):
            with transaction.atomic():
                config = LimiteIntercambioConfig.objects.get(
                    categoria=instance.cliente.categoria,
                    moneda=instance.moneda_destino
                )
                limite_cliente = LimiteIntercambioCliente.objects.select_for_update().get(
                    cliente=instance.cliente,
                    config=config
                )

                monto = instance.monto_destino
                limite_cliente.descontar(monto)

                # Guardar log
                LimiteIntercambioLog.objects.create(
                    transaccion=instance,
                    monto_descontado=monto
                )

        # 2) Si pasa a cancelado/anulado y ya tenía descuento → restaurar exactamente
        elif instance.estado in ESTADOS_RESTAURAN and log and log.monto_descontado > 0:
            with transaction.atomic():
                config = LimiteIntercambioConfig.objects.get(
                    categoria=instance.cliente.categoria,
                    moneda=instance.moneda_destino
                )
                limite_cliente = LimiteIntercambioCliente.objects.select_for_update().get(
                    cliente=instance.cliente,
                    config=config
                )

                # Devolver
                limite_cliente.limite_dia_actual += log.monto_descontado
                limite_cliente.limite_mes_actual += log.monto_descontado
                limite_cliente.save(update_fields=["limite_dia_actual", "limite_mes_actual"])

                # Marcar log como ya restaurado
                log.monto_descontado = Decimal("0")
                log.save()

    except Exception as e:
        logger.exception(f"Error en actualización de límite post transacción: {e}")
