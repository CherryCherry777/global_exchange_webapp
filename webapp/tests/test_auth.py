from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

User = get_user_model()

class AuthTests(TestCase):

    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'Testpass123',
            'password2': 'Testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirige después de registro
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_user_login(self):
        # Crear usuario
        user = User.objects.create_user(username='loginuser', password='Testpass123')
        login = self.client.login(username='loginuser', password='Testpass123')
        self.assertTrue(login)

    def test_user_logout(self):
        user = User.objects.create_user(username='logoutuser', password='Testpass123')
        self.client.login(username='logoutuser', password='Testpass123')
        response = self.client.get(reverse('logout'))
        # Cambia según tu comportamiento real:
        self.assertIn(response.status_code, [200, 302])

    def test_email_verification(self):
        # Crear usuario inactivo
        user = User.objects.create_user(
            username='verifyuser',
            email='verify@example.com',
            password='Testpass123',
            is_active=False
        )
        
        # Generar token de verificación
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        
        # Verificar email
        response = self.client.get(reverse('verify-email', kwargs={'uidb64': uid, 'token': token}))
        self.assertEqual(response.status_code, 302)  # Redirige después de verificación
        
        # Verificar que el usuario está activo
        user.refresh_from_db()
        self.assertTrue(user.is_active)