# Tests para métodos de cobro del cliente
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from webapp.models import Role, Cliente, Categoria, MedioCobro, ClienteUsuario

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
            tipoCliente="persona",
            nombre="Cliente Test",
            documento="12345678",
            correo="cliente@test.com",
            telefono="0981234567",
            direccion="Test Address 123",
            categoria=self.categoria
        )
        
        # Asociar cliente con usuario
        ClienteUsuario.objects.create(
            cliente=self.cliente,
            usuario=self.user
        )
        
    def test_my_cobro_methods_view_access(self):
        """Test acceso a vista de métodos de cobro del cliente"""
        self.client.login(username="test_user", password="testpass123")
        
        # Establecer cliente en sesión
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        response = self.client.get(reverse('my_cobro_methods'))
        
        # La vista puede redirigir si no hay métodos o mostrar la página
        self.assertIn(response.status_code, [200, 302])
        
    def test_add_cobro_method_billetera(self):
        """Test acceso a vista para agregar método de cobro tipo billetera"""
        self.client.login(username="test_user", password="testpass123")
        
        # Establecer cliente en sesión
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        # Verificar que la vista GET responde
        response = self.client.get(
            reverse('add_cobro_method', kwargs={'tipo': 'billetera'})
        )
        
        # La vista puede responder 200 (formulario) o 302 (redirección)
        self.assertIn(response.status_code, [200, 302])
        
    def test_add_cobro_method_cuenta_bancaria(self):
        """Test acceso a vista para agregar método de cobro tipo cuenta bancaria"""
        self.client.login(username="test_user", password="testpass123")
        
        # Establecer cliente en sesión
        session = self.client.session
        session['cliente_id'] = self.cliente.id
        session.save()
        
        # Verificar que la vista GET responde
        response = self.client.get(
            reverse('add_cobro_method', kwargs={'tipo': 'cuenta_bancaria'})
        )
        
        # La vista puede responder 200 (formulario) o 302 (redirección)
        self.assertIn(response.status_code, [200, 302])