from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Cliente, Categoria, ClienteUsuario
from webapp.forms import ClienteForm, ClienteUpdateForm

User = get_user_model()

class ClienteTests(TestCase):
    
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
        
        # Crear cliente de prueba
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            documento="12345678",
            tipoCliente="persona",
            categoria=self.categoria,
            estado=True
        )

    def test_create_cliente(self):
        """Prueba la creación de un nuevo cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('create_cliente'), {
            'nombre': 'Nuevo Cliente',
            'documento': '87654321',
            'tipoCliente': 'empresa',
            'categoria': self.categoria.id,
            'estado': True
        })
        
        self.assertEqual(response.status_code, 302)  # Redirige después de crear
        self.assertTrue(Cliente.objects.filter(documento='87654321').exists())

    def test_manage_clientes_view(self):
        """Prueba la vista de gestión de clientes"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_clientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_update_cliente(self):
        """Prueba la actualización de un cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('update_cliente', kwargs={'cliente_id': self.cliente.id}), {
            'nombre': 'Cliente Actualizado',
            'documento': '12345678',
            'tipoCliente': 'empresa',
            'categoria': self.categoria.id,
            'estado': True
        })
        
        self.assertEqual(response.status_code, 302)
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.nombre, 'Cliente Actualizado')

    def test_view_cliente(self):
        """Prueba la vista de detalle de cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('view_cliente', kwargs={'cliente_id': self.cliente.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cliente Test')

    def test_delete_cliente(self):
        """Prueba la eliminación de un cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('delete_cliente', kwargs={'cliente_id': self.cliente.id}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Cliente.objects.filter(id=self.cliente.id).exists())

    def test_cliente_form_valid(self):
        """Prueba que el formulario de cliente es válido con datos correctos"""
        form_data = {
            'nombre': 'Cliente Form Test',
            'documento': '11111111',
            'tipoCliente': 'persona',
            'categoria': self.categoria.id,
            'estado': True
        }
        form = ClienteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_cliente_form_invalid(self):
        """Prueba que el formulario de cliente es inválido con datos incorrectos"""
        form_data = {
            'nombre': '',  # Campo requerido vacío
            'documento': '12345678',  # Documento duplicado
            'tipoCliente': 'persona',
            'categoria': self.categoria.id,
            'estado': True
        }
        form = ClienteForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_cliente_update_form(self):
        """Prueba el formulario de actualización de cliente"""
        form_data = {
            'nombre': 'Cliente Actualizado',
            'documento': '12345678',
            'tipoCliente': 'empresa',
            'categoria': self.categoria.id,
            'estado': False
        }
        form = ClienteUpdateForm(data=form_data, instance=self.cliente)
        self.assertTrue(form.is_valid())

    def test_asignar_cliente_usuario(self):
        """Prueba la asignación de cliente a usuario"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('asignar_cliente_usuario'), {
            'cliente': self.cliente.id,
            'usuario': self.admin_user.id
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ClienteUsuario.objects.filter(
            cliente=self.cliente, 
            usuario=self.admin_user
        ).exists())

    def test_inactivar_cliente(self):
        """Prueba la inactivación de un cliente"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('inactivar_cliente', kwargs={'pk': self.cliente.id}))
        self.assertEqual(response.status_code, 302)
        
        self.cliente.refresh_from_db()
        self.assertFalse(self.cliente.estado)

    def test_activar_cliente(self):
        """Prueba la activación de un cliente"""
        # Primero inactivar el cliente
        self.cliente.estado = False
        self.cliente.save()
        
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.post(reverse('activar_cliente', kwargs={'pk': self.cliente.id}))
        self.assertEqual(response.status_code, 302)
        
        self.cliente.refresh_from_db()
        self.assertTrue(self.cliente.estado)
