from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Currency

User = get_user_model()

class CurrencyTests(TestCase):
    
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

    def test_manage_currencies_view(self):
        """Prueba la vista de gestión de monedas"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('currency_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Americano')

    def test_create_currency(self):
        """Prueba la creación de una nueva moneda"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('create_currency'), {
            'name': 'Euro',
            'code': 'EUR',
            'symbol': '€',
            'buy_rate': 800.00,
            'sell_rate': 810.00,
            'decimales_cotizacion': 2,
            'decimales_monto': 2,
            'flag_image': 'eu.png',
            'is_active': True
        })
        
        self.assertEqual(response.status_code, 200)  # O 302 si redirige
        self.assertTrue(Currency.objects.filter(code='EUR').exists())

    def test_toggle_currency(self):
        """Prueba la activación/desactivación de una moneda"""
        self.client.login(username='admin', password='testpass123')
        
        # Desactivar moneda
        response = self.client.post(reverse('toggle_currency'), {
            'currency_id': self.currency.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.currency.refresh_from_db()
        self.assertFalse(self.currency.is_active)

    def test_currency_model_str(self):
        """Prueba el método __str__ del modelo Currency"""
        expected_str = f"{self.currency.code} - {self.currency.name}"
        self.assertEqual(str(self.currency), expected_str)

    def test_currency_active_property(self):
        """Prueba la propiedad is_active del modelo Currency"""
        self.assertTrue(self.currency.is_active)
        
        self.currency.is_active = False
        self.currency.save()
        self.assertFalse(self.currency.is_active)

    def test_currency_rates(self):
        """Prueba las tasas de compra y venta de la moneda"""
        self.assertEqual(self.currency.buy_rate, 750.00)
        self.assertEqual(self.currency.sell_rate, 760.00)
        
        # Verificar que la tasa de venta es mayor que la de compra
        self.assertGreater(self.currency.sell_rate, self.currency.buy_rate)

    def test_currency_decimals(self):
        """Prueba los decimales de cotización y monto"""
        self.assertEqual(self.currency.decimales_cotizacion, 2)
        self.assertEqual(self.currency.decimales_monto, 2)

    def test_public_home_with_currencies(self):
        """Prueba que la página pública muestra las monedas activas"""
        response = self.client.get(reverse('public_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Americano')
        self.assertContains(response, 'USD')

    def test_currency_inactive_not_shown_public(self):
        """Prueba que las monedas inactivas no se muestran en la página pública"""
        # Desactivar la moneda
        self.currency.is_active = False
        self.currency.save()
        
        response = self.client.get(reverse('public_home'))
        self.assertEqual(response.status_code, 200)
        # La moneda inactiva no debería aparecer
        self.assertNotContains(response, 'Dólar Americano')

    def test_currency_update_rates(self):
        """Prueba la actualización de tasas de una moneda"""
        self.client.login(username='admin', password='testpass123')
        
        new_buy_rate = 780.00
        new_sell_rate = 790.00
        
        response = self.client.post(reverse('create_currency'), {
            'currency_id': self.currency.id,
            'buy_rate': new_buy_rate,
            'sell_rate': new_sell_rate
        })
        
        self.currency.refresh_from_db()
        self.assertEqual(self.currency.buy_rate, new_buy_rate)
        self.assertEqual(self.currency.sell_rate, new_sell_rate)

    def test_currency_validation(self):
        """Prueba la validación de datos de moneda"""
        # Crear moneda con datos inválidos
        with self.assertRaises(Exception):
            Currency.objects.create(
                name="",  # Nombre vacío
                code="",  # Código vacío
                symbol="",
                buy_rate=-100.00,  # Tasa negativa
                sell_rate=50.00,
                decimales_cotizacion=2,
                decimales_monto=2,
                is_active=True
            )

    def test_currency_unique_code(self):
        """Prueba que el código de moneda debe ser único"""
        # Intentar crear otra moneda con el mismo código
        with self.assertRaises(Exception):
            Currency.objects.create(
                name="Dólar Americano 2",
                code="USD",  # Código duplicado
                symbol="$",
                buy_rate=750.00,
                sell_rate=760.00,
                decimales_cotizacion=2,
                decimales_monto=2,
                is_active=True
            )
