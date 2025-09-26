from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Cliente, Categoria, ClienteUsuario

User = get_user_model()

class AssignClientsTests(TestCase):
    
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
        
        # Crear usuario empleado
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        employee_group = Group.objects.get_or_create(name="Empleado")[0]
        self.employee_user.groups.add(employee_group)
        
        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre="Categoría Test",
            descuento=0.100
        )
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            documento="12345678",
            tipoCliente="persona",
            categoria=self.categoria,
            estado=True
        )

    def test_assign_clients_view(self):
        """Prueba la vista de asignación de clientes a usuarios"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('assign_clients'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_assign_client_to_user(self):
        """Prueba la asignación de un cliente a un usuario"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('assign_clients'), {
            'cliente': self.cliente.id,
            'usuario': self.employee_user.id
        })
        
        self.assertEqual(response.status_code, 302)  # Redirige después de asignar
        self.assertTrue(ClienteUsuario.objects.filter(
            cliente=self.cliente,
            usuario=self.employee_user
        ).exists())

    def test_assign_client_duplicate(self):
        """Prueba que no se puede asignar el mismo cliente al mismo usuario dos veces"""
        # Crear asignación existente
        ClienteUsuario.objects.create(
            cliente=self.cliente,
            usuario=self.employee_user
        )
        
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('assign_clients'), {
            'cliente': self.cliente.id,
            'usuario': self.employee_user.id
        })
        
        # Verificar que solo existe una asignación
        self.assertEqual(ClienteUsuario.objects.filter(
            cliente=self.cliente,
            usuario=self.employee_user
        ).count(), 1)
