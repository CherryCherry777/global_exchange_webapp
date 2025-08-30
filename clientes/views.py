from clientes.decorators import permitir_permisos    # Importamos el decorador personalizado para controlar roles/permiso en las vistas.
from django.shortcuts import render, redirect, get_object_or_404           # Importamos render para devolver plantillas HTML con contexto.
from clientes.models import Cliente, ClienteUsuario  # Importamos los modelos que vamos a usar.
from webapp.models import CustomUser
from clientes.forms import ClienteForm
from django.contrib import messages
from django.http import JsonResponse

# Create your views here.

def es_admin(user):                                 # Función auxiliar para verificar si un usuario es admin.
    return user.is_authenticated and user.is_superuser  
    # Devuelve True si el usuario está autenticado y además es superusuario.

# --------------------------------------------
# Vista para listar todos los clientes
# --------------------------------------------
@permitir_permisos(['clientes.add_cliente', 'clientes.change_cliente', 'clientes.delete_cliente', 'clientes.view_cliente', 'clientes.add_clienteusuario', 'clientes.change_clienteusuario', 'clientes.delete_clienteusuario', 'clientes.view_clienteusuario'])      # Decorador que limita el acceso a usuarios con permisos específicos.
def manage_clientes(request):                       # Vista que lista todos los clientes.
    clientes = Cliente.objects.all()                # Consultamos todos los registros de la tabla Cliente.
    return render(request, "clientes/clientes.html", {"clientes": clientes})  
    # Retornamos la plantilla "clientes.html" pasando como contexto la lista de clientes.

# --------------------------------------------
# Vista para crear un cliente
# --------------------------------------------
@permitir_permisos(['clientes.add_cliente'])
def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)  # Crea un formulario con los datos enviados
        if form.is_valid():               # Valida que los datos sean correctos
            form.save()                   # Guarda el nuevo cliente en la base de datos
            messages.success(request, "Cliente creado exitosamente.")  # Mensaje de éxito
            form = ClienteForm()          # Reinicia el formulario vacío
        else:
            messages.error(request, "Por favor corrige los errores.")  # Mensaje de error si el form no es válido
    else:
        form = ClienteForm()              # Si es GET, crea un formulario vacío

    # Renderiza el template con el formulario
    return render(request, 'clientes/crear_cliente.html', {'form': form})

# --------------------------------------------
# Vista para inactivar un cliente
# --------------------------------------------
@permitir_permisos(['clientes.change_cliente', 'clientes.delete_clientes'])
def inactivar_cliente(request, pk):
    # Busca el cliente por ID o devuelve 404 si no existe
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.estado = False                # Cambia el estado a "inactivo"
    cliente.save()                        # Guarda el cambio en la base de datos
    # Mensaje de éxito
    messages.success(request, f"Cliente '{cliente.nombre}' inactivado correctamente.")
    # Redirige a la vista principal de gestión de clientes
    return redirect('manage_clientes')


# --------------------------------------------
# Vista para activar un cliente
# --------------------------------------------
@permitir_permisos(['clientes.change_cliente'])
def activar_cliente(request, pk):
    # Busca el cliente por ID o devuelve 404
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.estado = True                 # Cambia el estado a "activo"
    cliente.save()                        # Guarda el cambio
    # Mensaje de éxito
    messages.success(request, f"Cliente '{cliente.nombre}' activado correctamente.")
    # Redirige a la vista principal de gestión de clientes
    return redirect('manage_clientes')

# --------------------------------------------
# Vista para modificar un cliente
# --------------------------------------------
@permitir_permisos(['clientes.change_cliente'])
def modificar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "El cliente fue modificado correctamente.")
            return redirect("manage_clientes")
        else:
            messages.error(request, "Por favor corrige los errores.")
    else:
        form = ClienteForm(instance=cliente)

    return render(request, "clientes/modificar_cliente.html", {"form": form})