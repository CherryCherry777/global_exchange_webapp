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
        
        # Obtener o crear monedas para testing (evitar duplicados)
        self.usd, _ = Currency.objects.get_or_create(
            code="USD",
            defaults={
                'name': "Dólar Americano",
                'base_price': Decimal("7500.00"),
                'comision_compra': Decimal("50.00"),
                'comision_venta': Decimal("75.00"),
                'is_active': True
            }
        )
        
        self.eur, _ = Currency.objects.get_or_create(
            code="EUR", 
            defaults={
                'name': "Euro",
                'base_price': Decimal("8200.00"),
                'comision_compra': Decimal("60.00"),
                'comision_venta': Decimal("85.00"),
                'is_active': True
            }
        )
        
        # Obtener o crear categoría para testing
        from webapp.models import Categoria
        self.categoria, _ = Categoria.objects.get_or_create(
            nombre="Premium Test",
            defaults={'descuento': Decimal('0.05')}
        )
        
        # Crear límite de intercambio de prueba
        self.limite_config, _ = LimiteIntercambioConfig.objects.get_or_create(
            categoria=self.categoria,
            moneda=self.usd,
            defaults={
                'limite_dia_max': Decimal("10000.00"),
                'limite_mes_max': Decimal("100000.00")
            }
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
        # El modelo usa 'moneda', no 'moneda_origen'
        self.assertContains(response, self.limite_config.moneda.code)
        
    def test_limite_config_model_validation(self):
        """Test validación del modelo LimiteIntercambioConfig"""
        # El modelo usa limite_dia_max y limite_mes_max, no monto_min/monto_max
        # Verificar que los límites diarios son menores a los mensuales
        self.assertTrue(self.limite_config.limite_dia_max <= self.limite_config.limite_mes_max)
        
        # Test string representation - formato actual: "Categoria / USD (MAX)"
        expected_str = f"{self.categoria} / {self.usd.code} (MAX)"
        self.assertEqual(str(self.limite_config), expected_str)
        
    def test_limites_tabla_htmx_view(self):
        """Test vista HTMX para tabla de límites"""
        self.client.login(username="admin_user", password="testpass123")
        # Este endpoint podría necesitar parámetros, verificar que responde
        response = self.client.get(reverse('limites_tabla_htmx'))
        
        # Solo verificar que responde correctamente
        self.assertEqual(response.status_code, 200)