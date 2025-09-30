from .constants import *
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import ClienteForm, ClienteUpdateForm
from ..decorators import role_required, permitir_permisos
from ..models import Cliente, ClienteUsuario, Categoria

# -----------------------
# Cliente Management Views
# -----------------------

@login_required
@role_required("Administrador")
def manage_clientes(request):
    """Vista principal para gestionar clientes - Lista todos los clientes"""
    clientes = Cliente.objects.all().order_by('-fechaRegistro')
    
    # Filtros
    search_query = request.GET.get('search', '')
    categoria_filter = request.GET.get('categoria', '')
    estado_filter = request.GET.get('estado', '')
    
    if search_query:
        clientes = clientes.filter(
            models.Q(nombre__icontains=search_query) |
            models.Q(correo__icontains=search_query) |
            models.Q(documento__icontains=search_query)
        )
    
    if categoria_filter:
        clientes = clientes.filter(categoria=categoria_filter)
    
    if estado_filter:
        estado_bool = estado_filter == 'activo'
        clientes = clientes.filter(estado=estado_bool)
    
    # Calcular estadísticas
    total_clientes = Cliente.objects.count()
    clientes_activos = Cliente.objects.filter(estado=True).count()
    total_categorias = Categoria.objects.count()
    
    context = {
        'clients': clientes,
        'total_clients': total_clientes,
        'active_clients': clientes_activos,
        'search_query': search_query,
        'categoria_filter': categoria_filter,
        'estado_filter': estado_filter,
        'categorias': Categoria.objects.all(),
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'total_categorias': total_categorias,
    }
    
    return render(request, "webapp/clientes/manage_clients.html", context)

@login_required
@role_required("Administrador")
def modify_client(request, client_id):
    """Vista para modificar un cliente existente"""
    client = get_object_or_404(Cliente, id=client_id)
    
    if request.method == "POST":
        # Procesar formulario de modificación
        nombre = request.POST.get('nombre', '')
        razon_social = request.POST.get('razon_social', '')
        direccion = request.POST.get('direccion', '')
        tipo_cliente = request.POST.get('tipo_cliente', '')
        documento = request.POST.get('documento', '')
        ruc = request.POST.get('ruc', '')
        correo = request.POST.get('correo', '')
        telefono = request.POST.get('telefono', '')
        categoria_id = request.POST.get('categoria', '')
        estado = request.POST.get('estado') == 'on'
        
        try:
            # Actualizar campos del cliente
            client.nombre = nombre
            client.razonSocial = razon_social if razon_social else None
            client.direccion = direccion
            client.tipoCliente = tipo_cliente
            client.documento = documento
            client.ruc = ruc if ruc else None
            client.correo = correo
            client.telefono = telefono
            client.estado = estado
            
            # Actualizar categoría
            if categoria_id:
                categoria = Categoria.objects.get(id=categoria_id)
                client.categoria = categoria
            
            client.save()
            messages.success(request, f"Cliente '{client.nombre}' modificado correctamente.")
            return redirect("manage_clientes")
            
        except Exception as e:
            messages.error(request, f"Error al modificar el cliente: {str(e)}")
            return redirect("modify_client", client_id=client_id)
    
    # GET request - mostrar formulario
    categorias = Categoria.objects.all()
    
    context = {
        "client": client,
        "categorias": categorias,
    }
    
    return render(request, "webapp/clientes/modify_client.html", context)

@login_required
@role_required("Administrador")
def create_client(request):
    """Vista para crear un nuevo cliente"""
    if request.method == "POST":
        # Procesar formulario de creación
        nombre = request.POST.get('nombre', '')
        razon_social = request.POST.get('razon_social', '')
        direccion = request.POST.get('direccion', '')
        tipo = request.POST.get('tipo', '')
        documento = request.POST.get('documento', '')
        ruc = request.POST.get('ruc', '')
        correo = request.POST.get('correo', '')
        telefono = request.POST.get('telefono', '')
        categoria_id = request.POST.get('categoria', '')
        activo = request.POST.get('activo') == 'on'
        
        try:
            # Validar datos requeridos
            if not nombre or not direccion or not tipo or not documento or not correo or not telefono or not categoria_id:
                messages.error(request, "Todos los campos son requeridos.")
                return redirect("create_client")
            
            # Verificar si ya existe un cliente con el mismo documento
            if Cliente.objects.filter(documento=documento).exists():
                messages.error(request, "Ya existe un cliente con este documento.")
                return redirect("create_client")
            
            # Verificar si ya existe un cliente con el mismo correo
            if Cliente.objects.filter(correo=correo).exists():
                messages.error(request, "Ya existe un cliente con este correo.")
                return redirect("create_client")
            
            # Obtener categoría
            categoria = Categoria.objects.get(id=categoria_id)
            
            # Crear nuevo cliente
            client = Cliente.objects.create(
                nombre=nombre,
                razonSocial=razon_social if razon_social else None,
                direccion=direccion,
                tipoCliente=tipo,
                documento=documento,
                ruc=ruc if ruc else None,
                correo=correo,
                telefono=telefono,
                categoria=categoria,
                estado=activo
            )
            
            messages.success(request, f"Cliente '{client.nombre}' creado exitosamente.")
            return redirect("manage_clientes")
            
        except Categoria.DoesNotExist:
            messages.error(request, "La categoría seleccionada no existe.")
            return redirect("create_client")
        except Exception as e:
            messages.error(request, f"Error al crear el cliente: {str(e)}")
            return redirect("create_client")
    
    # GET request - mostrar formulario
    categorias = Categoria.objects.all()
    
    # Opciones de tipo de cliente
    tipo_choices = [
        ('Persona Natural', 'Persona Natural'),
        ('Persona Jurídica', 'Persona Jurídica'),
    ]
    
    context = {
        "categorias": categorias,
        "tipo_choices": tipo_choices,
    }
    
    return render(request, "webapp/clientes/create_client.html", context)

@login_required
@role_required("Administrador")
def create_cliente(request):
    """Vista para crear un nuevo cliente"""
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente '{cliente.nombre}' creado exitosamente.")
            return redirect("manage_clientes")
    else:
        form = ClienteForm()
    
    return render(request, "webapp/clientes/cliente_form.html", {
        'form': form,
        'title': 'Crear Cliente',
        'action': 'create'
    })

@login_required
@role_required("Administrador")
def update_cliente(request, cliente_id):
    """Vista para actualizar un cliente existente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == "POST":
        form = ClienteUpdateForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente '{cliente.nombre}' actualizado exitosamente.")
            return redirect("manage_clientes")
    else:
        form = ClienteUpdateForm(instance=cliente)
    
    return render(request, "webapp/clientes/cliente_form.html", {
        'form': form,
        'title': 'Editar Cliente',
        'action': 'update',
        'cliente': cliente
    })

@login_required
@role_required("Administrador")
def delete_cliente(request, cliente_id):
    """Vista para eliminar un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == "POST":
        cliente_nombre = cliente.nombre
        cliente.delete()
        messages.success(request, f"Cliente '{cliente_nombre}' eliminado exitosamente.")
        return redirect("manage_clientes")
    
    return render(request, "webapp/clientes/confirm_delete_cliente.html", {'cliente': cliente})

@login_required
@role_required("Administrador")
def view_cliente(request, cliente_id):
    """Vista para ver los detalles de un cliente"""
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    # Obtener usuarios asignados a este cliente
    usuarios_asignados = ClienteUsuario.objects.filter(cliente=cliente).select_related('usuario')
    
    context = {
        'cliente': cliente,
        'usuarios_asignados': usuarios_asignados,
    }
    
    return render(request, "webapp/clientes/view_cliente.html", context)

# --------------------------------------------
# Vista para inactivar un cliente
# --------------------------------------------
@permitir_permisos(['webapp.change_cliente', 'webapp.delete_cliente'])
def inactivar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.estado = False
    cliente.save()
    messages.success(request, f"Cliente '{cliente.nombre}' inactivado correctamente.")
    return redirect('manage_clientes')

# --------------------------------------------
# Vista para activar un cliente
# --------------------------------------------
@permitir_permisos(['webapp.change_cliente'])
def activar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.estado = True
    cliente.save()
    messages.success(request, f"Cliente '{cliente.nombre}' activado correctamente.")
    return redirect('manage_clientes')
