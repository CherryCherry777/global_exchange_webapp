"""
Este archivo indica que se auto-crearan grupos (roles) en el setup de la app
"""
from django.db.models.signals import post_migrate
from django.contrib.auth.models import Group, Permission
from django.contrib.auth import get_user_model
from django.dispatch import receiver

#esto automaticamente crea los grupos de permisos, y el admin por defecto
@receiver(post_migrate)
def create_default_roles_and_admin(sender, **kwargs):
    if sender.name == "webapp":
        # 1. Create groups
        regular_group, _ = Group.objects.get_or_create(name="Regular User")
        employee_group, _ = Group.objects.get_or_create(name="Employee")
        admin_group, _ = Group.objects.get_or_create(name="Administrator")

        # 2. Create default admin user
        User = get_user_model()
        username = "superadmin"
        password = "password12345"  # change this after first login
        email = "admin@example.com"

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, password=password, email=email)
            user.groups.add(admin_group)
            user.is_active = True
            user.save()
            print(f"Default admin user '{username}' created with password '{password}'")
        else:
            print(f"Default admin user '{username}' already exists")