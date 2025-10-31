# Tests para configuración de schedules (temporizadores)
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import Role, EmailScheduleConfig, LimiteIntercambioScheduleConfig, ExpiracionTransaccionConfig

User = get_user_model()

class ScheduleConfigTest(TestCase):
    
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
        
        # Crear configuraciones de prueba
        self.email_config = EmailScheduleConfig.objects.create(
            frequency="daily",
            hour=9,
            minute=0
        )
        
        self.limite_config = LimiteIntercambioScheduleConfig.objects.create(
            frequency="daily",
            hour=0,
            minute=0,
            is_active=True
        )
        
        self.expiracion_config = ExpiracionTransaccionConfig.objects.create(
            medio="cuenta_bancaria_negocio",
            minutos_expiracion=30
        )
        
    def test_manage_schedule_view_admin_access(self):
        """Test que admin puede acceder a gestión de schedules"""
        self.client.login(username="admin_user", password="testpass123")
        response = self.client.get(reverse('manage_schedule'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Configuración del Sistema")
        
    def test_email_schedule_config_model(self):
        """Test modelo EmailScheduleConfig"""
        self.assertEqual(self.email_config.frequency, "daily")
        self.assertEqual(self.email_config.hour, 9)
        self.assertEqual(self.email_config.minute, 0)
        
        # Test string representation
        expected_str = "Envío daily a las 09:00"
        self.assertEqual(str(self.email_config), expected_str)
        
    def test_limite_intercambio_schedule_config_model(self):
        """Test modelo LimiteIntercambioScheduleConfig"""
        self.assertEqual(self.limite_config.frequency, "daily")
        self.assertEqual(self.limite_config.hour, 0)
        self.assertEqual(self.limite_config.minute, 0)
        self.assertTrue(self.limite_config.is_active)
        
        # Test string representation
        expected_str = "(GLOBAL) Diario @ 00:00 | Activo"
        self.assertEqual(str(self.limite_config), expected_str)
        
    def test_expiracion_transaccion_config_model(self):
        """Test modelo ExpiracionTransaccionConfig"""
        self.assertEqual(self.expiracion_config.medio, "cuenta_bancaria_negocio")
        self.assertEqual(self.expiracion_config.minutos_expiracion, 30)
        
        # Test string representation 
        expected_str = "Transferencia → 30 min"
        self.assertEqual(str(self.expiracion_config), expected_str)