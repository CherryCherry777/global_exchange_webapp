from django.http import HttpResponseForbidden   # Importamos la respuesta HTTP 403 (Prohibido).
from functools import wraps                     # Importamos wraps para preservar metadatos de la vista decorada.

def permitir_permisos(permisos):                # Definimos el decorador, recibe una lista de permisos de Django.
    def decorador(vista_funcion):               # Función interna que recibe la vista a proteger.
        @wraps(vista_funcion)                   # Preserva nombre, docstring, módulo de la vista original.
        def wrapper(request, *args, **kwargs):  # Función que envuelve a la vista y aplica la lógica de permisos.
            
            # 1. Verificamos que el usuario esté autenticado
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Debes iniciar sesión.")
            
            # 2. Si es superusuario, accede siempre
            if request.user.is_superuser:
                return vista_funcion(request, *args, **kwargs)
            
            # 3. Verificamos que el usuario tenga **todos** los permisos requeridos
            #    `has_perm` espera un string del tipo "app_label.perm_codename"
            #    y `all()` exige que se cumplan todos los permisos en la lista.
            if all(request.user.has_perm(p) for p in permisos):
                return vista_funcion(request, *args, **kwargs)
            
            # 4. Si no cumple ninguna de las condiciones anteriores, devolvemos error 403
            return HttpResponseForbidden("No tienes permisos para acceder aquí.")
        
        return wrapper        # Devolvemos la función modificada
    return decorador          # Devolvemos el decorador listo para usarse

