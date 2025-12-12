from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Currency, Cotizacion

User = get_user_model()

class QuoteTests(TestCase):
    
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
        
        # Crear moneda de prueba
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
        
        # Crear cotización de prueba
        self.cotizacion = Cotizacion.objects.create(
            currency=self.currency,
            base_price=755.00,
            comision_compra=0.02,
            comision_venta=0.025,
            activo=True
        )

    def test_manage_quotes_view(self):
        """Prueba la vista de gestión de cotizaciones"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_quotes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Americano')

    def test_modify_quote_view(self):
        """Prueba la vista de modificación de cotización"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('modify_quote', kwargs={'quote_id': self.cotizacion.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Americano')

    def test_quote_model_str(self):
        """Prueba el método __str__ del modelo Cotizacion"""
        expected_str = f"{self.cotizacion.currency.code} - {self.cotizacion.currency.name}"
        self.assertEqual(str(self.cotizacion), expected_str)
