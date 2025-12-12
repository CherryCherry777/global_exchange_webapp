from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Categoria

User = get_user_model()

class CategoryTests(TestCase):
    
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
        
        # Crear categoría de prueba
        self.categoria = Categoria.objects.create(
            nombre="Categoría Test",
            descuento=0.100
        )

    def test_manage_categories_view(self):
        """Prueba la vista de gestión de categorías"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_categories'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Categoría Test')

    def test_modify_category_view(self):
        """Prueba la vista de modificación de categoría"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('modify_category', kwargs={'category_id': self.categoria.id}))
        self.assertEqual(response.status_code, 200)

    def test_category_model_str(self):
        """Prueba el método __str__ del modelo Categoria"""
        # El __str__ de Categoria incluye el descuento en porcentaje
        expected_str = f"{self.categoria.nombre} ({self.categoria.descuento * 100:.0f}%)"
        self.assertEqual(str(self.categoria), expected_str)
