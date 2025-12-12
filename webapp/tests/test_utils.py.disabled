from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Cliente, Categoria, ClienteUsuario
from webapp.utils import get_user_clients, get_client_users, calculate_discount

User = get_user_model()

class UtilsTests(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear grupos
        self.user_group = Group.objects.get_or_create(name="Usuario")[0]
        
        # Crear usuarios
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        # Crear categorías
        self.categoria1 = Categoria.objects.create(
            nombre="Categoría 1",
            descuento=0.100
        )
        
        # Crear clientes
        self.cliente1 = Cliente.objects.create(
            nombre="Cliente 1",
            documento="12345678",
            tipoCliente="persona",
            categoria=self.categoria1,
            estado=True
        )

    def test_get_user_clients(self):
        """Prueba la función get_user_clients"""
        # Crear asignación
        ClienteUsuario.objects.create(cliente=self.cliente1, usuario=self.user1)
        
        # Obtener clientes del usuario
        clients = get_user_clients(self.user1)
        
        # Verificar que se obtuvieron los clientes correctos
        self.assertEqual(len(clients), 1)
        self.assertIn(self.cliente1, clients)

    def test_get_client_users(self):
        """Prueba la función get_client_users"""
        # Crear asignación
        ClienteUsuario.objects.create(cliente=self.cliente1, usuario=self.user1)
        
        # Obtener usuarios del cliente
        users = get_client_users(self.cliente1)
        
        # Verificar que se obtuvieron los usuarios correctos
        self.assertEqual(len(users), 1)
        self.assertIn(self.user1, users)

    def test_calculate_discount(self):
        """Prueba la función calculate_discount"""
        # Calcular descuento para cliente con categoría
        discount = calculate_discount(self.cliente1, 1000.00)
        
        # Verificar que se calculó correctamente (10% de descuento)
        expected_discount = 1000.00 * 0.100
        self.assertEqual(discount, expected_discount)
