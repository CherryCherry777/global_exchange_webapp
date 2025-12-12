from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Cliente, Categoria, Currency, Cotizacion, TipoPago, TipoCobro

User = get_user_model()

class ViewsTests(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear grupos
        self.user_group = Group.objects.get_or_create(name="Usuario")[0]
        self.employee_group = Group.objects.get_or_create(name="Empleado")[0]
        self.admin_group = Group.objects.get_or_create(name="Administrador")[0]
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        self.regular_user.groups.add(self.user_group)
        
        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre="Categoría Test",
            descuento=0.100
        )
        
        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            documento="12345678",
            tipoCliente="persona",
            categoria=self.categoria,
            estado=True
        )
        
        # Crear moneda
        self.currency = Currency.objects.create(
            name="Dólar Americano",
            code="USD",
            symbol="$",
            buy_rate=750.00,
            sell_rate=760.00,
            decimales_cotizacion=2,
            decimales_monto=2,
            flag_image="us.png",
            is_active=True
        )
        
        # Crear cotización
        self.cotizacion = Cotizacion.objects.create(
            currency=self.currency,
            base_price=755.00,
            comision_compra=0.02,
            comision_venta=0.025,
            activo=True
        )
        
        # Crear método de pago global
        self.payment_method = TipoPago.objects.create(
            nombre="Visa",
            comision=0.025,
            activo=True
        )
        
        # Crear método de cobro global
        self.cobro_method = TipoCobro.objects.create(
            nombre="Transferencia Bancaria",
            comision=0.015,
            activo=True
        )

    def test_public_home_view(self):
        """Prueba la vista de página pública"""
        response = self.client.get(reverse('public_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Americano')

    def test_home_view_authenticated(self):
        """Prueba la vista de inicio para usuarios autenticados"""
        self.client.login(username='user', password='testpass123')
        
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_landing_view_admin(self):
        """Prueba la vista de landing para administradores"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Administrar Clientes')

    def test_profile_view(self):
        """Prueba la vista de perfil de usuario"""
        self.client.login(username='user', password='testpass123')
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_api_active_currencies_view(self):
        """Prueba la vista API de monedas activas"""
        response = self.client.get(reverse('api_active_currencies'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la respuesta es JSON
        import json
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
