# Tests para métodos de cobro del cliente
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from webapp.models import Role, Cliente, Categoria, MedioCobro, Billetera, CuentaBancaria

User = get_user_model()

class MetodosCobroClienteTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Crear usuario
        self.user = User.objects.create_user(
            username="test_user",
            email="test@test.com",
            password="testpass123"
        )
        
        # Crear categoría y cliente
        self.categoria = Categoria.objects.create(
            nombre="Premium",
            descuento=0.150  # 15% descuento
        )
        
        self.cliente = Cliente.objects.create(
            tipoCliente="persona_fisica",
            nombre="Cliente Test",
            documento="12345678",
            correo="cliente@test.com",
            telefono="0981234567",
            direccion="Test Address 123",
            categoria=self.categoria
        )
        
    def test_my_cobro_methods_view_access(self):
        """Test acceso a vista de métodos de cobro del cliente"""
        self.client.login(username="test_user", password="testpass123")
        response = self.client.get(reverse('my_cobro_methods'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mis Métodos de Cobro")
        
    def test_add_cobro_method_billetera(self):
        """Test agregar método de cobro tipo billetera"""
        self.client.login(username="test_user", password="testpass123")
        
        # Datos para crear billetera
        billetera_data = {
            'numero_celular': '+595981234567',
            'proveedor': 'Tigo Money',
            'pin': '1234'
        }
        
        response = self.client.post(
            reverse('add_cobro_method', kwargs={'tipo': 'billetera'}),
            data=billetera_data
        )
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó la billetera
        self.assertTrue(Billetera.objects.filter(
            numero_celular='+595981234567'
        ).exists())
        
    def test_add_cobro_method_cuenta_bancaria(self):
        """Test agregar método de cobro tipo cuenta bancaria"""
        self.client.login(username="test_user", password="testpass123")
        
        # Datos para crear cuenta bancaria
        cuenta_data = {
            'numero_cuenta': '1234567890',
            'banco': 'Banco Nacional',
            'alias_cbu': 'mi.cuenta.banco'
        }
        
        response = self.client.post(
            reverse('add_cobro_method', kwargs={'tipo': 'cuenta_bancaria'}),
            data=cuenta_data
        )
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó la cuenta
        self.assertTrue(CuentaBancaria.objects.filter(
            numero_cuenta='1234567890'
        ).exists())