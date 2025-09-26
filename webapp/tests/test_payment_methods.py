from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Cliente, Categoria, MedioPago, Tarjeta, Billetera, CuentaBancaria, Entidad, Currency
from webapp.forms import TarjetaForm, BilleteraForm, CuentaBancariaForm, MedioPagoForm

User = get_user_model()

class PaymentMethodTests(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre="Categoría Test",
            descuento=0.100
        )
        
        # Crear usuario administrador
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Crear grupo administrador
        self.admin_group = Group.objects.get_or_create(name="Administrador")[0]
        self.admin_user.groups.add(self.admin_group)
        
        # Crear cliente
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            documento="12345678",
            tipoCliente="persona_fisica",
            categoria=self.categoria,
            estado=True,
            correo="cliente@test.com",
            telefono="0981234567",
            direccion="Dirección Test"
        )

    def test_manage_client_payment_methods(self):
        """Prueba la vista de gestión de medios de pago por cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('my_payment_methods'))
        self.assertEqual(response.status_code, 200)

    def test_manage_client_payment_methods_detail(self):
        """Prueba la vista de detalle de medios de pago de un cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('my_payment_methods'))
        self.assertEqual(response.status_code, 200)

    def test_add_payment_method_tarjeta(self):
        """Prueba agregar un medio de pago tipo tarjeta"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'tipo': 'tarjeta'}))
        self.assertEqual(response.status_code, 200)

    def test_add_payment_method_billetera(self):
        """Prueba agregar un medio de pago tipo billetera"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'tipo': 'billetera'}))
        self.assertEqual(response.status_code, 200)

    def test_add_payment_method_cuenta_bancaria(self):
        """Prueba agregar un medio de pago tipo cuenta bancaria"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'tipo': 'cuenta_bancaria'}))
        self.assertEqual(response.status_code, 200)


    def test_tarjeta_form_valid(self):
        """Prueba que el formulario de tarjeta es válido"""
        form_data = {
            'numero_tokenizado': 'tok_123456789',
            'fecha_vencimiento': '2025-12-31',
            'ultimos_digitos': '1234'
        }
        form = TarjetaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_tarjeta_form_invalid(self):
        """Prueba que el formulario de tarjeta es inválido con datos incorrectos"""
        form_data = {
            'numero_tokenizado': 'tok_123456789',
            'fecha_vencimiento': '2025-12-31',
            'ultimos_digitos': '123'  # Solo 3 dígitos, debe ser 4
        }
        form = TarjetaForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_billetera_form_valid(self):
        """Prueba que el formulario de billetera es válido"""
        # Crear entidad para la billetera
        entidad = Entidad.objects.get_or_create(
            nombre="Tigo Money Test",
            defaults={'tipo': 'billetera', 'activo': True}
        )[0]
        
        form_data = {
            'numero_celular': '0981234567',
            'entidad': entidad.id
        }
        form = BilleteraForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cuenta_bancaria_form_valid(self):
        """Prueba que el formulario de cuenta bancaria es válido"""
        # Crear entidad para la cuenta bancaria
        entidad = Entidad.objects.get_or_create(
            nombre="Banco Test",
            defaults={'tipo': 'banco', 'activo': True}
        )[0]
        
        form_data = {
            'numero_cuenta': '1234567890',
            'alias_cbu': 'alias.test',
            'entidad': entidad.id
        }
        form = CuentaBancariaForm(data=form_data)
        self.assertTrue(form.is_valid())


    def test_medio_pago_form_valid(self):
        """Prueba que el formulario de medio de pago es válido"""
        # Crear moneda para el medio de pago
        moneda = Currency.objects.get_or_create(
            code="PYG",
            defaults={
                'name': 'Guaraní Paraguayo',
                'symbol': '₲',
                'is_active': True,
                'base_price': 1.0,
                'comision_venta': 0.02,
                'comision_compra': 0.02
            }
        )[0]
        
        form_data = {
            'nombre': 'Visa Principal',
            'moneda': moneda.id
        }
        form = MedioPagoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_create_medio_pago_tarjeta(self):
        """Prueba la creación completa de un medio de pago tipo tarjeta"""
        # Crear medio de pago base
        medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='tarjeta',
            nombre='Visa Test',
            activo=True
        )
        
        # Crear tarjeta asociada
        tarjeta = Tarjeta.objects.create(
            medio_pago=medio_pago,
            numero_tokenizado='tok_123456789',
            fecha_vencimiento='2025-12-31',
            ultimos_digitos='1234'
        )
        
        self.assertTrue(MedioPago.objects.filter(id=medio_pago.id).exists())
        self.assertTrue(Tarjeta.objects.filter(id=tarjeta.id).exists())
        self.assertEqual(tarjeta.medio_pago, medio_pago)

    def test_toggle_medio_pago(self):
        """Prueba la activación/desactivación de un medio de pago"""
        medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='tarjeta',
            nombre='Visa Test',
            activo=True
        )
        
        self.client.login(username='admin', password='testpass123')
        
        # Desactivar
        response = self.client.post(reverse('my_payment_methods'), {
            'action': 'toggle',
            'medio_pago_id': medio_pago.id
        })
        
        self.assertEqual(response.status_code, 302)
        medio_pago.refresh_from_db()
        self.assertFalse(medio_pago.activo)

    def test_delete_medio_pago(self):
        """Prueba la eliminación de un medio de pago"""
        medio_pago = MedioPago.objects.create(
            cliente=self.cliente,
            tipo='tarjeta',
            nombre='Visa Test',
            activo=True
        )
        
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('my_payment_methods'), {
            'action': 'delete',
            'medio_pago_id': medio_pago.id
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MedioPago.objects.filter(id=medio_pago.id).exists())