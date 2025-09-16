# signals.py
from django.conf import settings
from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from .models import Role
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
    tipos = ["billetera", "cheque", "cuenta_bancaria", "tarjeta"]
    
    for nombre in tipos:
        TipoPago.objects.get_or_create(nombre=nombre, defaults=defaults)