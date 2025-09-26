from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import TipoCobro

User = get_user_model()

class GlobalCobroMethodTests(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Crear grupo administrador
        self.admin_group = Group.objects.get_or_create(name="Administrador")[0]
        self.admin_user.groups.add(self.admin_group)
        
        # Crear método de cobro global de prueba
        self.cobro_method = TipoCobro.objects.create(
            nombre="Transferencia Bancaria",
            comision=0.015,
            activo=True
        )

    def test_manage_cobro_methods_view(self):
        """Prueba la vista de gestión de métodos de cobro globales"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_cobro_methods'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transferencia Bancaria')

    def test_modify_cobro_method_view(self):
        """Prueba la vista de modificación de método de cobro global"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('modify_cobro_method', kwargs={'cobro_method_id': self.cobro_method.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transferencia Bancaria')

    def test_cobro_method_model_str(self):
        """Prueba el método __str__ del modelo TipoCobro"""
        expected_str = self.cobro_method.nombre
        self.assertEqual(str(self.cobro_method), expected_str)
