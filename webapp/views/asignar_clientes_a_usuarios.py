from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import AsignarClienteForm
from ..decorators import role_required, permitir_permisos
from ..models import Cliente, ClienteUsuario
from .constants import *

# --------------------------------------------
# Vista para asignar clientes a usuarios (Posible vista nueva)
# --------------------------------------------

@login_required
@role_required("Administrador")
def view_client(request, client_id):
    """Vista para visualizar los datos de un cliente"""
    try:
        client = Cliente.objects.get(id=client_id)
        # Obtener usuarios asignados a través del modelo intermedio
        usuarios_asignados = User.objects.filter(clienteusuario__cliente=client)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect("manage_clientes")
    
    context = {
        "client": client,
        "usuarios_asignados": usuarios_asignados,
    }
    
    return render(request, "webapp/asignar_clientes_a_usuarios/view_client.html", context)


@login_required
@role_required("Administrador")
def assign_clients(request):
    """Vista para administrar asignaciones de clientes a usuarios"""
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "assign":
            cliente_id = request.POST.get("cliente_id")
            usuario_id = request.POST.get("usuario_id")
            
            try:
                cliente = Cliente.objects.get(id=cliente_id)
                usuario = User.objects.get(id=usuario_id)
                
                # Verificar si ya existe la asignación
                if ClienteUsuario.objects.filter(cliente=cliente, usuario=usuario).exists():
                    messages.info(request, f"El usuario '{usuario.username}' ya está asignado al cliente '{cliente.nombre}'.")
                else:
                    ClienteUsuario.objects.create(cliente=cliente, usuario=usuario)
                    messages.success(request, f"Cliente '{cliente.nombre}' asignado al usuario '{usuario.username}' correctamente.")
                    
            except (Cliente.DoesNotExist, User.DoesNotExist):
                messages.error(request, "Error al asignar el cliente.")
        
        elif action == "unassign":
            asignacion_id = request.POST.get("asignacion_id")
            
            try:
                asignacion = ClienteUsuario.objects.get(id=asignacion_id)
                cliente_nombre = asignacion.cliente.nombre
                usuario_nombre = asignacion.usuario.username
                asignacion.delete()
                messages.success(request, f"Cliente '{cliente_nombre}' desasignado del usuario '{usuario_nombre}' correctamente.")
                
            except ClienteUsuario.DoesNotExist:
                messages.error(request, "Error al desasignar el cliente.")
        
        return redirect("assign_clients")
    
    # GET request - mostrar la página
    clientes = Cliente.objects.filter(estado=True).order_by('nombre')
    usuarios = User.objects.filter(is_active=True).order_by('username')
    asignaciones = ClienteUsuario.objects.select_related('cliente', 'usuario').order_by('-fecha_asignacion')
    
    # Calcular métricas
    total_users = User.objects.filter(is_active=True).count()
    total_clients = Cliente.objects.filter(estado=True).count()
    
    context = {
        "clientes": clientes,
        "usuarios": usuarios,
        "asignaciones": asignaciones,
        "total_users": total_users,
        "total_clients": total_clients,
    }
    
    return render(request, "webapp/asignar_clientes_a_usuarios/assign_clients.html", context)


# --------------------------------------------
# Vista para asignar clientes a usuarios (Posible vista vieja)
# --------------------------------------------
@permitir_permisos(['webapp.add_clienteusuario', 'webapp.view_clienteusuario'])
def asignar_cliente_usuario(request):
    if request.method == "POST":
        form = AsignarClienteForm(request.POST)
        if form.is_valid():
            try:
                ClienteUsuario.objects.create(
                    cliente=form.cleaned_data['cliente'],
                    usuario=form.cleaned_data['usuario']
                )
                messages.success(request, f"Cliente '{form.cleaned_data['cliente'].nombre}' asignado exitosamente al usuario '{form.cleaned_data['usuario'].username}'.")
                return redirect('asignar_cliente_usuario')
            except IntegrityError:
                messages.error(request, "Esta asignación ya existe.")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = AsignarClienteForm()
    
    asignaciones = ClienteUsuario.objects.select_related('cliente', 'usuario').all().order_by('-fecha_asignacion')
    
    return render(request, 'webapp/asignar_clientes_a_usuarios/asignar_cliente_usuario.html', {
        'form': form,
        'asignaciones': asignaciones
    })

# --------------------------------------------
# Vista para desasignar cliente de usuario (Posible vista vieja)
# --------------------------------------------
@permitir_permisos(['webapp.delete_clienteusuario'])
def desasignar_cliente_usuario(request, asignacion_id):
    asignacion = get_object_or_404(ClienteUsuario, id=asignacion_id)
    cliente_nombre = asignacion.cliente.nombre
    usuario_username = asignacion.usuario.username
    
    asignacion.delete()
    messages.success(request, f"Cliente '{cliente_nombre}' desasignado del usuario '{usuario_username}'.")
    
    return redirect('asignar_cliente_usuario')