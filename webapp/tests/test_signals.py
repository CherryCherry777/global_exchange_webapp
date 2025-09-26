from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.signals import assign_default_role

User = get_user_model()

class SignalTests(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear grupos
        self.user_group = Group.objects.get_or_create(name="Usuario")[0]

    def test_assign_default_role_on_user_creation(self):
        """Prueba que se asigna el rol por defecto al crear un usuario"""
        # Crear usuario
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Verificar que se asignó el rol por defecto
        self.assertTrue(user.groups.filter(name="Usuario").exists())

    def test_assign_default_role_existing_user(self):
        """Prueba que no se asigna rol por defecto a usuarios existentes"""
        # Crear usuario
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Limpiar grupos
        user.groups.clear()
        
        # Guardar el usuario (simular actualización)
        user.save()
        
        # Verificar que no se asignó el rol por defecto
        self.assertFalse(user.groups.filter(name="Usuario").exists())

    def test_assign_default_role_signal_function(self):
        """Prueba la función del signal directamente"""
        # Crear usuario
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Limpiar grupos
        user.groups.clear()
        
        # Llamar la función del signal directamente
        assign_default_role(sender=User, instance=user, created=True)
        
        # Verificar que se asignó el rol por defecto
        self.assertTrue(user.groups.filter(name="Usuario").exists())
