from clientes.decorators import permitir_permisos    # Importamos el decorador personalizado para controlar roles/permiso en las vistas.
from django.shortcuts import render, redirect           # Importamos render para devolver plantillas HTML con contexto.
from clientes.models import Cliente, ClienteUsuario  # Importamos los modelos que vamos a usar.
from clientes.forms import ClienteForm
from django.contrib import messages

# Create your views here.   # Comentario por defecto que pone Django en views.py

def es_admin(user):                                 # Función auxiliar para verificar si un usuario es admin.
    return user.is_authenticated and user.is_superuser  
    # Devuelve True si el usuario está autenticado y además es superusuario.

@permitir_permisos(['clientes.add_cliente', 'clientes.change_cliente', 'clientes.delete_cliente', 'clientes.view_cliente', 'clientes.add_clienteusuario', 'clientes.change_clienteusuario', 'clientes.delete_clienteusuario', 'clientes.view_clienteusuario'])      # Decorador que limita el acceso a usuarios con permisos específicos.
def manage_clientes(request):                       # Vista que lista todos los clientes.
    clientes = Cliente.objects.all()                # Consultamos todos los registros de la tabla Cliente.
    return render(request, "clientes/clientes.html", {"clientes": clientes})  
    # Retornamos la plantilla "clientes.html" pasando como contexto la lista de clientes.

def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado exitosamente.")
            return redirect('clientes')  # nombre de la url donde está la lista
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        form = ClienteForm()

    return render(request, 'webapp/crear_cliente.html', {'form': form})

from .models import Cliente

def clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'webapp/clientes.html', {'clientes': clientes})