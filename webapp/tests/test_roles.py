from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

class RoleTests(TestCase):

    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(name="Administrador")
        self.employee_group, _ = Group.objects.get_or_create(name="Empleado")
        self.user = User.objects.create_user(username='roleuser', password='pass123')

    def test_assign_default_role(self):
        self.assertTrue(self.user.groups.filter(name="Usuario").exists())

    def test_add_role(self):
        self.user.groups.add(self.employee_group)
        self.assertTrue(self.user.groups.filter(name="Empleado").exists())

    def test_remove_role(self):
        self.user.groups.add(self.employee_group)
        self.user.groups.remove(self.employee_group)
        self.assertFalse(self.user.groups.filter(name="Empleado").exists())