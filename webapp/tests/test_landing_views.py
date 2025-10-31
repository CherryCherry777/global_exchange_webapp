# Tests para las vistas de landing y página de administrar métodos
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Role, Cliente, Categoria, ClienteUsuario
from webapp.templatetags.permissions_tags import has_perms, is_usuario_asociado

User = get_user_model()

class LandingViewsTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Obtener grupos y roles existentes (creados por migrations)
        admin_group, _ = Group.objects.get_or_create(name="Administrador")
        analyst_group, _ = Group.objects.get_or_create(name="Analista")
        
        self.admin_role, _ = Role.objects.get_or_create(group=admin_group)
        self.analyst_role, _ = Role.objects.get_or_create(group=analyst_group)
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="testpass123"
        )
        self.admin_user.groups.add(admin_group)
        
        self.regular_user = User.objects.create_user(
            username="regular_user", 
            email="regular@test.com",
            password="testpass123"
        )
        
        # Crear categoría y cliente para usuario asociado
        self.categoria = Categoria.objects.create(
            nombre="Test Category",
            descuento=0.100  # 10% descuento
        )
        
        self.cliente = Cliente.objects.create(
            tipoCliente="persona_fisica",
            nombre="Test Cliente",
            documento="12345678",
            correo="cliente@test.com",
            telefono="0981234567",
            direccion="Test Address 123",
            categoria=self.categoria
        )
        
        # Crear relación cliente-usuario para regular_user
        self.cliente_usuario = ClienteUsuario.objects.create(
            cliente=self.cliente,
            usuario=self.regular_user
        )
        
    def test_landing_page_admin_access(self):
        """Test que admin puede acceder al landing con panel admin"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse('landing'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel de administración")
        self.assertContains(response, "Gestión centralizada del sistema")
        
    def test_landing_page_regular_user_access(self):
        """Test que usuario regular ve sección de usuario"""
        self.client.login(username="regular_user", password="testpass123")
        response = self.client.get(reverse('landing'))
        
        self.assertEqual(response.status_code, 200)
        # El usuario tiene acceso pero necesita seleccionar un cliente
        self.assertContains(response, "Ningún cliente seleccionado")
        self.assertContains(response, "Cambiar de Cliente")
        
    def test_administar_metodos_pago_view_authenticated(self):
        """Test nueva vista administar_metodos_pago requiere autenticación"""
        self.client.login(username="regular_user", password="testpass123")
        response = self.client.get(reverse('administar_metodos_pago'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrar métodos de pago y cobro")
        self.assertContains(response, "Administrar Métodos de Pago")
        self.assertContains(response, "Administrar Métodos de Cobro")
        
    def test_administar_metodos_pago_view_unauthenticated(self):
        """Test nueva vista redirige a login si no está autenticado"""
        response = self.client.get(reverse('administar_metodos_pago'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
    def test_landing_context_variables(self):
        """Test que el landing tiene las variables de contexto correctas"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse('landing'))
        
        self.assertIn('usuarios_activos', response.context)
        self.assertIn('monedas_activas', response.context)
        self.assertIn('clientes_activos', response.context)
        self.assertIn('entidades_activas', response.context)