from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.urls import reverse
from webapp.decorators import role_required, permitir_permisos
from webapp.models import Cliente, Categoria

User = get_user_model()

class DecoratorTests(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.factory = RequestFactory()
        
        # Crear grupos
        self.admin_group = Group.objects.get_or_create(name="Administrador")[0]
        self.employee_group = Group.objects.get_or_create(name="Empleado")[0]
        self.user_group = Group.objects.get_or_create(name="Usuario")[0]
        
        # Crear usuarios
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.admin_user.groups.add(self.admin_group)
        
        self.employee_user = User.objects.create_user(
            username='employee',
            email='employee@test.com',
            password='testpass123'
        )
        self.employee_user.groups.add(self.employee_group)
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        self.regular_user.groups.add(self.user_group)
        
        # Crear categoría y cliente para pruebas
        self.categoria = Categoria.objects.create(
            nombre="Categoría Test",
            descuento=0.100
        )
        
        self.cliente = Cliente.objects.create(
            nombre="Cliente Test",
            documento="12345678",
            tipoCliente="persona",
            categoria=self.categoria,
            estado=True
        )

    def test_role_required_admin_access(self):
        """Prueba que un administrador puede acceder a funciones que requieren rol admin"""
        @role_required("Administrador")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Acceso permitido")

    def test_role_required_employee_denied(self):
        """Prueba que un empleado no puede acceder a funciones que requieren rol admin"""
        @role_required("Administrador")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.employee_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_role_required_regular_user_denied(self):
        """Prueba que un usuario regular no puede acceder a funciones que requieren rol admin"""
        @role_required("Administrador")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.regular_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_role_required_employee_access(self):
        """Prueba que un empleado puede acceder a funciones que requieren rol empleado"""
        @role_required("Empleado")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.employee_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Acceso permitido")

    def test_role_required_admin_can_access_employee_functions(self):
        """Prueba que un admin puede acceder a funciones de empleado"""
        @role_required("Empleado")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Acceso permitido")

    def test_permitir_permisos_with_permission(self):
        """Prueba que un usuario con permisos puede acceder"""
        # Asignar permiso al admin
        from django.contrib.auth.models import Permission
        permission = Permission.objects.get(codename='add_cliente')
        self.admin_user.user_permissions.add(permission)
        
        @permitir_permisos(['webapp.add_cliente'])
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Acceso permitido")

    def test_permitir_permisos_without_permission(self):
        """Prueba que un usuario sin permisos no puede acceder"""
        @permitir_permisos(['webapp.add_cliente'])
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.regular_user  # Usuario sin permisos
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_permitir_permisos_multiple_permissions(self):
        """Prueba que un usuario necesita todos los permisos especificados"""
        from django.contrib.auth.models import Permission
        permission1 = Permission.objects.get(codename='add_cliente')
        permission2 = Permission.objects.get(codename='change_cliente')
        
        # Asignar solo uno de los permisos
        self.admin_user.user_permissions.add(permission1)
        
        @permitir_permisos(['webapp.add_cliente', 'webapp.change_cliente'])
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_permitir_permisos_all_permissions(self):
        """Prueba que un usuario con todos los permisos puede acceder"""
        from django.contrib.auth.models import Permission
        permission1 = Permission.objects.get(codename='add_cliente')
        permission2 = Permission.objects.get(codename='change_cliente')
        
        # Asignar ambos permisos
        self.admin_user.user_permissions.add(permission1, permission2)
        
        @permitir_permisos(['webapp.add_cliente', 'webapp.change_cliente'])
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "Acceso permitido")

    def test_role_required_anonymous_user(self):
        """Prueba que un usuario anónimo no puede acceder"""
        @role_required("Usuario")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = None  # Usuario anónimo
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_permitir_permisos_anonymous_user(self):
        """Prueba que un usuario anónimo no puede acceder con permisos"""
        @permitir_permisos(['webapp.add_cliente'])
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = None  # Usuario anónimo
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_role_required_invalid_role(self):
        """Prueba que un rol inválido no permite acceso"""
        @role_required("RolInexistente")
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos

    def test_permitir_permisos_invalid_permission(self):
        """Prueba que un permiso inválido no permite acceso"""
        @permitir_permisos(['webapp.permiso_inexistente'])
        def test_view(request):
            return HttpResponse("Acceso permitido")
        
        request = self.factory.get('/test/')
        request.user = self.admin_user
        
        response = test_view(request)
        self.assertEqual(response.status_code, 302)  # Redirige por falta de permisos
