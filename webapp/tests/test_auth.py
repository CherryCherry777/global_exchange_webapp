from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(TestCase):

    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
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