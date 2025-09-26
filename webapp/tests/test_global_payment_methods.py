from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from webapp.models import TipoPago

User = get_user_model()

class GlobalPaymentMethodTests(TestCase):
    
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
        
        # Crear método de pago global de prueba
        self.payment_method = TipoPago.objects.create(
            nombre="Visa",
            comision=0.025,
            activo=True
        )

    def test_manage_payment_methods_view(self):
        """Prueba la vista de gestión de métodos de pago globales"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('manage_payment_methods'))
        # Asserts básicos
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visa')
        
        # Asserts adicionales para mayor cobertura
        self.assertContains(response, 'Administrar Métodos de Pago Globales')
        self.assertContains(response, 'Total Métodos')
        self.assertContains(response, 'Lista de Métodos de Pago Globales')
        
        # Verificar que el contexto contiene los datos esperados
        self.assertIn('payment_methods', response.context)
        self.assertIn('total_payment_methods', response.context)
        
        # Verificar que el método de pago está en el contexto
        payment_methods = response.context['payment_methods']
        self.assertTrue(payment_methods.filter(nombre='Visa').exists())

    def test_modify_payment_method_view(self):
        """Prueba la vista de modificación de método de pago global"""
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get(reverse('modify_payment_method', kwargs={'payment_method_id': self.payment_method.id}))
        # Asserts básicos
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visa')
        
        # Asserts adicionales
        self.assertContains(response, 'Modificar Método de Pago Global')
        self.assertContains(response, 'Comisión (%)')
        
        # Verificar que el contexto contiene el método de pago
        self.assertIn('payment_method', response.context)
        self.assertEqual(response.context['payment_method'], self.payment_method)
        
        # Verificar que los valores están pre-cargados en el formulario
        self.assertContains(response, '0,03')  # Valor de comisión (formato con coma)

    def test_payment_method_model_str(self):
        """Prueba el método __str__ del modelo TipoPago"""
        expected_str = self.payment_method.nombre
        self.assertEqual(str(self.payment_method), expected_str)
        
        # Asserts adicionales para el modelo
        self.assertIsNotNone(self.payment_method.id)
        self.assertTrue(self.payment_method.activo)
        self.assertEqual(self.payment_method.comision, 0.025)
        
    def test_payment_method_creation(self):
        """Prueba la creación de un método de pago"""
        # Verificar que el método se creó correctamente en setUp
        self.assertIsNotNone(self.payment_method.id)
        self.assertEqual(self.payment_method.nombre, 'Visa')
        self.assertEqual(self.payment_method.comision, 0.025)
        self.assertTrue(self.payment_method.activo)
        
    def test_payment_method_update(self):
        """Prueba la actualización de un método de pago"""
        # Actualizar el método
        self.payment_method.nombre = 'Mastercard'
        self.payment_method.comision = 0.03
        self.payment_method.save()
        
        # Verificar los cambios
        self.payment_method.refresh_from_db()
        self.assertEqual(self.payment_method.nombre, 'Mastercard')
        self.assertEqual(float(self.payment_method.comision), 0.03)
        
    def test_payment_method_deactivation(self):
        """Prueba la desactivación de un método de pago"""
        # Desactivar el método
        self.payment_method.activo = False
        self.payment_method.save()
        
        # Verificar el cambio
        self.payment_method.refresh_from_db()
        self.assertFalse(self.payment_method.activo)
