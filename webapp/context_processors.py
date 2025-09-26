from django.contrib.auth.models import Group
from .models import ClienteUsuario

def admin_status(request):
    is_admin = False
    if request.user.is_authenticated:
        is_admin = request.user.groups.filter(name='Administrador').exists()
    return {'is_admin': is_admin}

def clientes_disponibles(request):
    if not request.user.is_authenticated:
        return {"clientes_disponibles": []}

    # Traer los clientes asociados al usuario
    clientes = (
        ClienteUsuario.objects
        .filter(usuario=request.user)
        .select_related("cliente")
    )
    return {"clientes_disponibles": [cu.cliente for cu in clientes]}