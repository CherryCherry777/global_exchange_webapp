from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Cliente, Categoria, MedioPago, Tarjeta, Billetera, CuentaBancaria, Cheque
from webapp.forms import TarjetaForm, BilleteraForm, CuentaBancariaForm, ChequeForm, MedioPagoForm

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
            tipoCliente="persona",
            categoria=self.categoria,
            estado=True
        )

    def test_manage_client_payment_methods(self):
        """Prueba la vista de gestión de medios de pago por cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_client_payment_methods'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_manage_client_payment_methods_detail(self):
        """Prueba la vista de detalle de medios de pago de un cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_client_payment_methods_detail', 
                                        kwargs={'cliente_id': self.cliente.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nombre)

    def test_add_payment_method_tarjeta(self):
        """Prueba agregar un medio de pago tipo tarjeta"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'cliente_id': self.cliente.id, 'tipo': 'tarjeta'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar Tarjeta')

    def test_add_payment_method_billetera(self):
        """Prueba agregar un medio de pago tipo billetera"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'cliente_id': self.cliente.id, 'tipo': 'billetera'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar Billetera')

    def test_add_payment_method_cuenta_bancaria(self):
        """Prueba agregar un medio de pago tipo cuenta bancaria"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'cliente_id': self.cliente.id, 'tipo': 'cuenta_bancaria'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar Cuenta Bancaria')

    def test_add_payment_method_cheque(self):
        """Prueba agregar un medio de pago tipo cheque"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('add_payment_method', 
                                        kwargs={'cliente_id': self.cliente.id, 'tipo': 'cheque'}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar Cheque')

    def test_tarjeta_form_valid(self):
        """Prueba que el formulario de tarjeta es válido"""
        form_data = {
            'numero_tokenizado': 'tok_123456789',
            'banco': 'Banco Test',
            'fecha_vencimiento': '2025-12-31',
            'ultimos_digitos': '1234'
        }
        form = TarjetaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_tarjeta_form_invalid(self):
        """Prueba que el formulario de tarjeta es inválido con datos incorrectos"""
        form_data = {
            'numero_tokenizado': 'tok_123456789',
            'banco': 'Banco Test',
            'fecha_vencimiento': '2025-12-31',
            'ultimos_digitos': '123'  # Solo 3 dígitos, debe ser 4
        }
        form = TarjetaForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_billetera_form_valid(self):
        """Prueba que el formulario de billetera es válido"""
        form_data = {
            'numero_celular': '0981234567',
            'proveedor': 'Tigo Money'
        }
        form = BilleteraForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cuenta_bancaria_form_valid(self):
        """Prueba que el formulario de cuenta bancaria es válido"""
        form_data = {
            'numero_cuenta': '1234567890',
            'banco': 'Banco Test',
            'alias_cbu': 'alias.test'
        }
        form = CuentaBancariaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cheque_form_valid(self):
        """Prueba que el formulario de cheque es válido"""
        form_data = {
            'numero_cheque': 'CHQ001',
            'banco_emisor': 'Banco Test',
            'fecha_vencimiento': '2025-12-31',
            'monto': 1000.00
        }
        form = ChequeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cheque_form_invalid_monto(self):
        """Prueba que el formulario de cheque es inválido con monto negativo"""
        form_data = {
            'numero_cheque': 'CHQ001',
            'banco_emisor': 'Banco Test',
            'fecha_vencimiento': '2025-12-31',
            'monto': -100.00  # Monto negativo
        }
        form = ChequeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_medio_pago_form_valid(self):
        """Prueba que el formulario de medio de pago es válido"""
        form_data = {
            'nombre': 'Visa Principal'
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
            banco='Banco Test',
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
        response = self.client.post(reverse('manage_client_payment_methods_detail', 
                                          kwargs={'cliente_id': self.cliente.id}), {
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
        
        response = self.client.post(reverse('manage_client_payment_methods_detail', 
                                          kwargs={'cliente_id': self.cliente.id}), {
            'action': 'delete',
            'medio_pago_id': medio_pago.id
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MedioPago.objects.filter(id=medio_pago.id).exists())
