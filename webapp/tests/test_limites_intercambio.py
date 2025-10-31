# Tests para límites de intercambio
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Role, Currency, LimiteIntercambioConfig
from decimal import Decimal

User = get_user_model()

class LimitesIntercambioTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Obtener grupo y rol admin existente (creado por migrations)
        admin_group, _ = Group.objects.get_or_create(name="Administrador")
        self.admin_role, _ = Role.objects.get_or_create(group=admin_group)
        
        # Crear usuario admin
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@test.com", 
            password="testpass123"
        )
        self.admin_user.groups.add(admin_group)
        
        # Crear monedas para testing
        self.usd = Currency.objects.create(
            code="USD",
            name="Dólar Americano",
            base_price=Decimal("7500.00"),
            comision_compra=Decimal("50.00"),
            comision_venta=Decimal("75.00"),
            is_active=True
        )
        
        self.eur = Currency.objects.create(
            code="EUR", 
            name="Euro",
            base_price=Decimal("8200.00"),
            comision_compra=Decimal("60.00"),
            comision_venta=Decimal("85.00"),
            is_active=True
        )
        
        # Crear límite de intercambio de prueba
        self.limite_config = LimiteIntercambioConfig.objects.create(
            moneda_origen=self.usd,
            moneda_destino=self.eur,
            monto_max=Decimal("10000.00"),
            monto_min=Decimal("100.00")
        )
        
    def test_limites_list_view_admin_access(self):
        """Test que admin puede acceder a la lista de límites"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse('limites_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Límites de Intercambio")
        
    def test_limite_config_edit_view(self):
        """Test edición de configuración de límites"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(
            reverse('limite_config_edit', kwargs={'config_id': self.limite_config.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.limite_config.moneda_origen))
        
    def test_limite_config_model_validation(self):
        """Test validación del modelo LimiteIntercambioConfig"""
        # Test que monto_min debe ser menor que monto_max
        self.assertTrue(self.limite_config.monto_min < self.limite_config.monto_max)
        
        # Test string representation
        expected_str = f"Límite {self.usd.code} -> {self.eur.code}: {self.limite_config.monto_min} - {self.limite_config.monto_max}"
        self.assertEqual(str(self.limite_config), expected_str)
        
    def test_limites_tabla_htmx_view(self):
        """Test vista HTMX para tabla de límites"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse('limites_tabla_htmx'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.usd.code)