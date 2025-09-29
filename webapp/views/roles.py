from .constants import *
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from ..decorators import role_required
from ..models import Role

# ---------------------------------------------
# Administracion de roles (Posible vista nueva)
# ---------------------------------------------

@login_required
@role_required("Administrador")
def modify_users(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == "POST":
        # Verificar si es una solicitud de eliminación de rol
        if 'role_id' in request.POST:
            role_id = request.POST.get('role_id')
            try:
                role = Group.objects.get(id=role_id)
                user.groups.remove(role)
                messages.success(request, f"Rol '{role.name}' eliminado del usuario '{user.username}' correctamente.")
            except Group.DoesNotExist:
                messages.error(request, "El rol especificado no existe.")
            return redirect("modify_users", user_id=user_id)
        
        # Procesar formulario de modificación
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        username = request.POST.get('username', '')
        is_active = request.POST.get('is_active') == 'on'
        
        # Actualizar datos del usuario
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.username = username
        user.is_active = is_active
        user.save()
        
        messages.success(request, f"Usuario '{user.username}' modificado correctamente.")
        return redirect("manage_users")
    
    # Obtener roles del usuario
    user_roles = user.groups.all()
    
    context = {
        "user": user,
        "user_roles": user_roles,
    }
    
    return render(request, "webapp/modify_user.html", context)

@login_required
@role_required("Administrador")
def manage_roles(request):
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "remove_permission":
            role_id = request.POST.get("role_id")
            permission_id = request.POST.get("permission_id")
            
            try:
                role = Group.objects.get(id=role_id)
                permission = Permission.objects.get(id=permission_id)
                role.permissions.remove(permission)
                messages.success(request, f"Permiso '{permission.name}' eliminado del rol '{role.name}' correctamente.")
            except (Group.DoesNotExist, Permission.DoesNotExist):
                messages.error(request, "Error al eliminar el permiso.")
        
        elif action == "toggle_role_status":
            role_id = request.POST.get("role_id")
            
            try:
                role = Group.objects.get(id=role_id)
                
                # Verificar si el rol tiene usuarios activos
                has_active_users = role.user_set.filter(is_active=True).exists()
                
                if has_active_users:
                    # Si tiene usuarios activos, desactivamos el rol
                    # Removemos el rol del usuario actual para simular la desactivación
                    if request.user in role.user_set.all():
                        role.user_set.remove(request.user)
                        messages.success(request, f"Rol '{role.name}' desactivado correctamente.")
                    else:
                        messages.info(request, f"Rol '{role.name}' ya estaba desactivado para tu usuario.")
                else:
                    # Si no tiene usuarios activos, lo activamos asignándolo al usuario actual
                    if request.user.is_authenticated:
                        role.user_set.add(request.user)
                        messages.success(request, f"Rol '{role.name}' activado correctamente.")
                    else:
                        messages.error(request, "No se pudo activar el rol: usuario no autenticado.")
                    
            except Group.DoesNotExist:
                messages.error(request, "Error al actualizar el estado del rol.")
        
        return redirect("manage_roles")
    
    roles = Group.objects.all()
    
    # Calcular métricas
    total_roles = Group.objects.count()
    active_roles = Group.objects.filter(user__is_active=True).distinct().count()
    
    # Agregar información de estado a cada rol
    roles_with_status = []
    for role in roles:
        # Un rol se considera activo si tiene al menos un usuario activo asignado
        # En una implementación real, podrías tener un campo 'is_active' en el modelo Group
        role.is_active = role.user_set.filter(is_active=True).exists()
        
        # Para roles protegidos (como Administrador), siempre los consideramos activos
        if role.name == 'Administrador':
            role.is_active = True
            
        roles_with_status.append(role)
    
    context = {
        "roles": roles_with_status,
        "total_roles": total_roles,
        "active_roles": active_roles,
    }
    
    return render(request, "webapp/manage_roles.html", context)

@login_required
@role_required("Administrador")
def modify_role(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    
    if request.method == "POST":
        # Verificar si es una solicitud de eliminación de permiso
        if 'permission_id' in request.POST:
            permission_id = request.POST.get('permission_id')
            try:
                permission = Permission.objects.get(id=permission_id)
                role.permissions.remove(permission)
                messages.success(request, f"Permiso '{permission.name}' eliminado del rol '{role.name}' correctamente.")
            except Permission.DoesNotExist:
                messages.error(request, "El permiso especificado no existe.")
            return redirect("modify_role", role_id=role_id)
        
        # Verificar si es una solicitud de eliminación del rol
        if request.POST.get('action') == 'delete_role':
            # Proteger el rol Administrador
            if role.name == 'Administrador':
                messages.error(request, "No se puede eliminar el rol 'Administrador'.")
                return redirect("modify_role", role_id=role_id)
            
            role_name = role.name
            role.delete()
            messages.success(request, f"Rol '{role_name}' eliminado correctamente.")
            return redirect("manage_roles")
        
        # Procesar formulario de modificación
        role_name = request.POST.get('role_name', '')
        is_active = request.POST.get('is_active') == 'on'
        
        role.name = role_name
        role.save()
        
        messages.success(request, f"Rol '{role.name}' modificado correctamente.")
        return redirect("manage_roles")
    
    role_permissions = role.permissions.all()
    all_permissions = Permission.objects.all()
    
    # Agregar información de estado al rol
    role.is_active = role.user_set.filter(is_active=True).exists()
    
    context = {
        "role": role,
        "role_permissions": role_permissions,
        "all_permissions": all_permissions,
    }
    
    return render(request, "webapp/modify_role.html", context)

@login_required
@role_required("Administrador")
def create_role(request):
    if request.method == "POST":
        role_name = request.POST.get('role_name', '').strip()
        is_protected = request.POST.get('is_protected') == 'on'
        permissions = request.POST.getlist('permissions')
        
        # Validar que el nombre no esté vacío
        if not role_name:
            messages.error(request, "El nombre del rol es obligatorio.")
            return redirect("create_role")
        
        # Verificar que el nombre no exista
        if Group.objects.filter(name=role_name).exists():
            messages.error(request, f"Ya existe un rol con el nombre '{role_name}'.")
            return redirect("create_role")
        
        try:
            # Crear el nuevo rol
            new_role = Group.objects.create(name=role_name)
            
            # Asignar permisos si se seleccionaron
            if permissions:
                permission_objects = Permission.objects.filter(id__in=permissions)
                new_role.permissions.set(permission_objects)
            
            messages.success(request, f"Rol '{role_name}' creado correctamente.")
            return redirect("manage_roles")
            
        except Exception as e:
            messages.error(request, f"Error al crear el rol: {str(e)}")
            return redirect("create_role")
    
    # GET request - mostrar formulario
    all_permissions = Permission.objects.all()
    
    context = {
        "all_permissions": all_permissions,
    }
    
    return render(request, "webapp/create_role.html", context)


# ------------------------------------------------------------
# Role / Permission Management (Posiblemente la vista antigua)
# ------------------------------------------------------------

def get_highest_role_tier(user):
    user_roles = [g.name for g in user.groups.all()]
    if not user_roles:
        return 0  # No roles
    return min(ROLE_TIERS.get(r, 99) for r in user_roles)


@login_required
@role_required("Administrador")
def delete_role(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if role.name in PROTECTED_ROLES:
        messages.error(request, f"No puede eliminar el rol '{role.name}'.")
    else:
        role.delete()
        messages.success(request, f"El rol '{role.name}' fue eliminado exitosamente.")
    return redirect("role_list")


@login_required
@role_required("Administrador")
def confirm_delete_role(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if role.name in PROTECTED_ROLES:
        messages.error(request, f"No puede eliminar el rol '{role.name}'.")
        return redirect("manage_roles")

    if request.method == "POST":
        role.delete()
        messages.success(request, f"El rol '{role.name}' fue eliminado exitosamente.")
        return redirect("manage_roles")

    return render(request, "webapp/confirm_delete_role.html", {"role": role})


@login_required
@role_required("Administrador")
def update_role_permissions(request, role_id):
    role = get_object_or_404(Group, id=role_id)
    if request.method == "POST":
        selected_perms = request.POST.getlist("permissions")
        role.permissions.set(selected_perms)
        messages.success(request, f"Permisos actualizados para el rol '{role.name}'.")
    return redirect("role_list")