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
            base_price=750.00,
            comision_venta=1.0,
            comision_compra=1.0,
            decimales_cotizacion=2,
            decimales_monto=2,
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
            'base_price': 800.00,
            'comision_venta': 1.0,
            'comision_compra': 1.0,
            'decimales_cotizacion': 2,
            'decimales_monto': 2,
            'flag_image': 'eu.png',
            'is_active': True
        })
        
        self.assertEqual(response.status_code, 302)  # Redirige después de crear
        self.assertTrue(Currency.objects.filter(code='EUR').exists())

    def test_toggle_currency(self):
        """Prueba la activación/desactivación de una moneda"""
        self.client.login(username='admin', password='testpass123')
        
        # Desactivar moneda
        response = self.client.post(reverse('toggle_currency'), {
            'currency_id': self.currency.id
        })
        
        self.assertEqual(response.status_code, 302)  # Redirige después de toggle
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
        self.assertEqual(self.currency.base_price, 750.00)
        self.assertEqual(self.currency.comision_venta, 1.0)
        
        # Verificar que la comisión de venta es mayor que la de compra
        self.assertGreaterEqual(self.currency.comision_venta, self.currency.comision_compra)

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
        new_base_price = 780.00
        new_comision_venta = 1.5
        new_comision_compra = 1.2
        
        # Actualizar directamente en el modelo
        self.currency.base_price = new_base_price
        self.currency.comision_venta = new_comision_venta
        self.currency.comision_compra = new_comision_compra
        self.currency.save()
        
        # Verificar que las tasas se actualizaron
        self.currency.refresh_from_db()
        self.assertEqual(float(self.currency.base_price), new_base_price)
        self.assertEqual(float(self.currency.comision_venta), new_comision_venta)
        self.assertEqual(float(self.currency.comision_compra), new_comision_compra)

    def test_currency_validation(self):
        """Prueba la validación de datos de moneda"""
        # Crear moneda con código duplicado (esto debería fallar)
        with self.assertRaises(Exception):
            Currency.objects.create(
                name="Dólar Duplicado",
                code="USD",  # Código duplicado
                symbol="$",
                base_price=750.00,
                comision_venta=1.0,
                comision_compra=1.0,
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
                base_price=750.00,
                comision_venta=1.0,
                comision_compra=1.0,
                decimales_cotizacion=2,
                decimales_monto=2,
                is_active=True
            )

    def test_create_currency_view(self):
        """Prueba la vista de creación de moneda"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('create_currency'))
        self.assertEqual(response.status_code, 200)

    def test_modify_currency_view(self):
        """Prueba la vista de modificación de moneda"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('modify_currency', kwargs={'currency_id': self.currency.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Americano')