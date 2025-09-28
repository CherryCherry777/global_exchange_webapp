from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from ..decorators import role_required

# ---------------------------------------------
# Asignación de roles (Posible vista nueva)
# ---------------------------------------------

@login_required
@role_required("Administrador")
def manage_user_roles(request):
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "add_role":
            user_id = request.POST.get("user_id")
            role_id = request.POST.get("role_id")
            
            try:
                user = User.objects.get(id=user_id)
                role = Group.objects.get(id=role_id)
                
                # Verificar si el usuario ya tiene este rol
                if user.groups.filter(id=role_id).exists():
                    messages.info(request, f"El usuario '{user.username}' ya tiene el rol '{role.name}'.")
                else:
                    user.groups.add(role)
                    messages.success(request, f"Rol '{role.name}' asignado al usuario '{user.username}' correctamente.")
                    
            except (User.DoesNotExist, Group.DoesNotExist):
                messages.error(request, "Error al asignar el rol.")
        
        elif action == "remove_role":
            user_id = request.POST.get("user_id")
            role_name = request.POST.get("role_name")
            
            try:
                user = User.objects.get(id=user_id)
                role = Group.objects.get(name=role_name)
                
                user.groups.remove(role)
                messages.success(request, f"Rol '{role_name}' eliminado del usuario '{user.username}' correctamente.")
                
            except (User.DoesNotExist, Group.DoesNotExist):
                messages.error(request, "Error al eliminar el rol.")
        
        return redirect("manage_user_roles")
    
    # GET request - mostrar la página
    users = User.objects.all().order_by('username')
    all_roles = Group.objects.all().order_by('name')
    
    # Calcular métricas
    total_users = User.objects.count()
    total_roles = Group.objects.count()
    
    context = {
        "users": users,
        "all_roles": all_roles,
        "total_users": total_users,
        "total_roles": total_roles,
    }
    
    return render(request, "webapp/manage_user_roles.html", context)



# ------------------------------------------
# User Role Management (Posible vista vieja)
# ------------------------------------------
# Assign roles to users

@login_required
@role_required("Administrador")
def user_role_list(request):
    users = User.objects.all().prefetch_related("groups")
    all_roles = Group.objects.all()
    return render(request, "webapp/manage_user_roles.html", {
        "users": users,
        "all_roles": all_roles,
    })

@login_required
def manage_user_roles(request):
    users = User.objects.all()
    roles_list = Group.objects.all()

    # Determine current user's highest-tier role
    current_user_roles = request.user.groups.all()
    current_user_tier = min(ROLE_TIERS.get(r.name, 99) for r in current_user_roles) if current_user_roles else 99

    # Prepare data for template
    user_roles_data = []
    for u in users:
        roles_info = []
        user_role_names = [g.name for g in u.groups.all()]

        for r in u.groups.all():
            role_tier = ROLE_TIERS.get(r.name, 99)
            # Can remove if not removing own highest-tier role
            can_remove = not (u == request.user and role_tier >= current_user_tier)
            roles_info.append({
                "role": r,
                "can_remove": can_remove
            })

        user_roles_data.append({
            "user": u,
            "roles_info": roles_info,
            "user_role_names": user_role_names
        })

    return render(request, "webapp/manage_user_roles.html", {
        "user_roles_data": user_roles_data,
        "roles_list": roles_list
    })


@login_required
@role_required("Administrador")
def add_role_to_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        role_name = request.POST.get("role")
        if role_name:
            group = get_object_or_404(Group, name=role_name)
            if group.name not in [g.name for g in user.groups.all()]:
                user.groups.add(group)
                messages.success(request, f"Rol '{group.name}' asignado a '{user.username}'.")
            else:
                messages.info(request, f"El usuario ya tiene el rol '{group.name}'.")
        return redirect("manage_user_roles")

@login_required
@role_required("Administrador")
def remove_role_from_user(request, user_id, role_name):
    user = get_object_or_404(User, id=user_id)
    group = get_object_or_404(Group, name=role_name)

    # Check tiers before removal
    current_user_roles = request.user.groups.all()
    current_user_tier = min(ROLE_TIERS.get(r.name, 99) for r in current_user_roles) if current_user_roles else 99
    role_tier = ROLE_TIERS.get(group.name, 99)

    # Only prevent removing own highest-tier role
    if not (user == request.user and role_tier >= current_user_tier):
        user.groups.remove(group)

    return redirect("manage_user_roles")

    # Determine tiers
    current_user_roles = request.user.groups.all()
    current_user_tier = min(ROLE_TIERS.get(r.name, 99) for r in current_user_roles) if current_user_roles else 99
    target_user_roles = user_to_edit.groups.all()
    target_user_highest_tier = min(ROLE_TIERS.get(r.name, 99) for r in target_user_roles) if target_user_roles else 99

    # Prevent removing protected roles or higher-tier roles than current user
    if role_to_remove.name in PROTECTED_ROLES:
        messages.error(request, f"You cannot remove the {role_to_remove.name} role.")
    elif ROLE_TIERS.get(role_to_remove.name, 99) > current_user_tier:
        messages.error(request, "You cannot remove a role higher than your own.")
    elif user_to_edit == request.user and ROLE_TIERS.get(role_to_remove.name, 99) == current_user_tier:
        messages.error(request, "You cannot remove your own highest-tier role.")
    elif role_to_remove not in user_to_edit.groups.all():
        messages.warning(request, f"{user_to_edit.username} does not have the {role_to_remove.name} role.")
    else:
        user_to_edit.groups.remove(role_to_remove)
        messages.success(request, f"{role_to_remove.name} removed from {user_to_edit.username}.")

    return redirect("manage_user_roles")