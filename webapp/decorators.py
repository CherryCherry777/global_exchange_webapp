"""
decorators pueden ser aplicados a diferentes vistas para soportar elementos HTTP
"""
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from functools import wraps

def role_required(role_name):
    def decorator(view_func):
        def check_role(user):
            return user.groups.filter(name=role_name).exists()
        return user_passes_test(check_role)(view_func)
    return decorator

def permitir_permisos(permisos):
    """
    Decorador que permite acceso a usuarios con permisos específicos o rol de Administrador.
    """
    def decorador(vista_funcion):
        @wraps(vista_funcion)
        def wrapper(request, *args, **kwargs):
            
            # 1. Verificamos que el usuario esté autenticado
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Debes iniciar sesión.")
            
            # 2. Si es superusuario, accede siempre
            if request.user.is_superuser:
                return vista_funcion(request, *args, **kwargs)
            
            # 3. Si tiene rol de Administrador, accede siempre
            if request.user.groups.filter(name="Administrador").exists():
                return vista_funcion(request, *args, **kwargs)
            
            # 4. Verificamos que el usuario tenga **todos** los permisos requeridos
            if all(request.user.has_perm(p) for p in permisos):
                return vista_funcion(request, *args, **kwargs)
            
            # 5. Si no cumple ninguna de las condiciones anteriores, devolvemos error 403
            return HttpResponseForbidden("No tienes permisos para acceder aquí.")
        
        return wrapper
    return decorador

