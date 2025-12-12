# Tests para entidades de pago y cobro
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Role, Entidad

User = get_user_model()

class EntidadesPagoCobroTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Obtener grupo y rol admin existente (creado por migrations)
        admin_group, _ = Group.objects.get_or_create(name="Administrador")
        self.admin_role, _ = Role.objects.get_or_create(group=admin_group)
        
        # Crear usuario admin
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="testpass123"
        )
        self.admin_user.groups.add(admin_group)
        
        # Crear entidad de prueba
        self.entidad = Entidad.objects.create(
            nombre="Banco Test",
            tipo="banco",
            activo=True
        )
        
    def test_entidad_list_view_admin_access(self):
        """Test que admin puede acceder a lista de entidades"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse('entidad_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administrar Entidades")
        self.assertContains(response, self.entidad.nombre)
        
    def test_entidad_create_view(self):
        """Test crear nueva entidad"""
        self.client.login(username="admin_user", password="testpass123")
        
        entidad_data = {
            'nombre': 'Nueva Entidad',
            'tipo': 'banco',
            'activo': True
        }
        
        response = self.client.post(reverse('entidad_add'), data=entidad_data)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó la entidad
        self.assertTrue(Entidad.objects.filter(nombre='Nueva Entidad').exists())
        
    def test_entidad_update_view(self):
        """Test actualizar entidad existente"""
        self.client.login(username="admin_user", password="testpass123")
        
        updated_data = {
            'nombre': 'Banco Test Actualizado',
            'tipo': 'banco',
            'activo': True
        }
        
        response = self.client.post(
            reverse('entidad_edit', kwargs={'pk': self.entidad.pk}),
            data=updated_data
        )
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se actualizó
        self.entidad.refresh_from_db()
        self.assertEqual(self.entidad.nombre, 'Banco Test Actualizado')
        
    def test_entidad_toggle_view(self):
        """Test toggle activo/inactivo de entidad"""
        self.client.login(username="admin_user", password="testpass123")
        
        # Verificar estado inicial
        self.assertTrue(self.entidad.activo)
        
        # Toggle activo
        response = self.client.post(
            reverse('entidad_toggle', kwargs={'pk': self.entidad.pk})
        )
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        
        # Verificar que cambió el estado
        self.entidad.refresh_from_db()
        self.assertFalse(self.entidad.activo)
        
    def test_entidad_model_str_representation(self):
        """Test representación string del modelo Entidad"""
        expected_str = f"{self.entidad.nombre} ({self.entidad.get_tipo_display()})"
        self.assertEqual(str(self.entidad), expected_str)