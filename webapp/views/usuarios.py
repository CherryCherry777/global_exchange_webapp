from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from ..decorators import role_required

# -----------------------------
# User CRUD (class-based views)
# -----------------------------

class UserListView(ListView):
    model = User
    template_name = 'webapp/user_list.html'
    context_object_name = 'users'

class UserCreateView(CreateView):
    model = User
    template_name = 'webapp/user_form.html'
    fields = ['username', 'password', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        # Hash password before saving
        form.instance.set_password(form.instance.password)
        return super().form_valid(form)

class UserUpdateView(UpdateView):
    model = User
    template_name = 'webapp/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name']
    success_url = reverse_lazy('user_list')

class UserDeleteView(DeleteView):
    model = User
    template_name = 'webapp/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')


# ---------------
# Managing users
# ---------------

@login_required
@role_required("Administrador")
def manage_users(request):
    users = User.objects.all()

    # Calcular métricas
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    if request.method == "POST":
        action = request.POST.get("action")
        user_id = request.POST.get("user_id")
        if not user_id:
            messages.error(request, "No se especificó un usuario válido.")
            return redirect("manage_users")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
            return redirect("manage_users")

        # Evitar desactivar admins o tu propio usuario si quieres
        if user.is_superuser:
            messages.error(request, "No puede modificar un usuario administrador.")
            return redirect("manage_users")

        if action == "toggle_user":
            if user == request.user:
                messages.error(request, "No puede desactivar su propio usuario.")
                return redirect("manage_users")

            user.is_active = not user.is_active
            user.save()
            messages.success(
                request,
                f"Usuario '{user.username}' {'activado' if user.is_active else 'desactivado'}."
            )
        
        return redirect("manage_users")

    context = {
        "users": users,
        "total_users": total_users,
        "active_users": active_users,
    }
    
    return render(request, "webapp/manage_users.html", context)

@login_required
@role_required("Administrador")
def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Evitar activar/desactivar admins o tu propio usuario
    if user.is_superuser:
        messages.error(request, "No puede modificar un usuario administrador.")
        return redirect("manage_users")
    
    if user == request.user:
        messages.error(request, "No puede modificar su propio usuario.")
        return redirect("manage_users")
    
    user.is_active = True
    user.save()
    messages.success(request, f"Usuario '{user.username}' activado correctamente.")
    
    return redirect("manage_users")

@login_required
@role_required("Administrador")
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Evitar activar/desactivar admins o tu propio usuario
    if user.is_superuser:
        messages.error(request, "No puede modificar un usuario administrador.")
        return redirect("manage_users")
    
    if user == request.user:
        messages.error(request, "No puede modificar su propio usuario.")
        return redirect("manage_users")
    
    user.is_active = False
    user.save()
    messages.success(request, f"Usuario '{user.username}' desactivado correctamente.")
    
    return redirect("manage_users")

@login_required
@role_required("Administrador")
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    # Optional protection: prevent deleting self
    if user != request.user:
        user.delete()
    return redirect("manage_users")


@login_required
@role_required("Administrador")
def confirm_delete_user(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user_obj.delete()
        messages.success(request, f"Usuario '{user_obj.username}' eliminado exitosamente!")
        return redirect("manage_users")
    return render(request, "webapp/confirm_delete_user.html", {"user_obj": user_obj})


@login_required
@role_required("Administrador")
def modify_users(request, user_id):
    user_obj = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        # Get form data
        new_username = request.POST.get("username", user_obj.username)
        new_email = request.POST.get("email", user_obj.email)
        new_first_name = request.POST.get("first_name", user_obj.first_name)
        new_last_name = request.POST.get("last_name", user_obj.last_name)
        
        # Validate username uniqueness (only if it's different from current)
        if new_username != user_obj.username:
            if User.objects.filter(username=new_username).exists():
                messages.error(request, f"El nombre de usuario '{new_username}' ya existe. Por favor, elige otro.")
                roles = Group.objects.all()
                user_roles = {g.name for g in user_obj.groups.all()}
                return render(request, "webapp/modify_users.html", {
                    "user_obj": user_obj,
                    "roles": roles,
                    "user_roles": user_roles,
                    "ROLE_TIERS": {"Administrador": 3, "Empleado": 2, "Usuario": 1}
                })
        
        # Validate email uniqueness (only if it's different from current)
        if new_email != user_obj.email:
            if User.objects.filter(email=new_email).exists():
                messages.error(request, f"El email '{new_email}' ya está en uso. Por favor, elige otro.")
                roles = Group.objects.all()
                user_roles = {g.name for g in user_obj.groups.all()}
                return render(request, "webapp/modify_users.html", {
                    "user_obj": user_obj,
                    "roles": roles,
                    "user_roles": user_roles,
                    "ROLE_TIERS": {"Administrador": 3, "Empleado": 2, "Usuario": 1}
                })
        
        # Update basic info
        user_obj.username = new_username
        user_obj.email = new_email
        user_obj.first_name = new_first_name
        user_obj.last_name = new_last_name
        
        try:
            user_obj.save()
        except Exception as e:
            messages.error(request, f"Error al guardar los cambios: {str(e)}")
            roles = Group.objects.all()
            user_roles = {g.name for g in user_obj.groups.all()}
            return render(request, "webapp/modify_users.html", {
                "user_obj": user_obj,
                "roles": roles,
                "user_roles": user_roles,
                "ROLE_TIERS": {"Administrador": 3, "Empleado": 2, "Usuario": 1}
            })

        # Role management
        selected_roles = request.POST.getlist("roles")  # list of role names
        current_user_roles = {g.name for g in request.user.groups.all()}
        highest_current_tier = min([ROLE_TIERS.get(r, 99) for r in current_user_roles], default=99)

        # Add/remove roles while respecting tier logic
        for role in Group.objects.all():
            role_name = role.name
            if role_name in selected_roles and role_name not in {g.name for g in user_obj.groups.all()}:
                # Can only add role lower than or equal to your own highest tier
                if ROLE_TIERS.get(role_name, 99) >= highest_current_tier:
                    user_obj.groups.add(role)
            elif role_name not in selected_roles and role_name in {g.name for g in user_obj.groups.all()}:
                # Can only remove role lower than your own highest tier
                if ROLE_TIERS.get(role_name, 99) > highest_current_tier or user_obj != request.user:
                    user_obj.groups.remove(role)

        messages.success(request, f"Usuario '{user_obj.username}' actualizado exitosamente.")
        return redirect("manage_users")

    roles = Group.objects.all()
    user_roles = {g.name for g in user_obj.groups.all()}

    return render(request, "webapp/modify_users.html", {
        "user_obj": user_obj,
        "roles": roles,
        "user_roles": user_roles,
        "ROLE_TIERS": {"Administrador": 3, "Empleado": 2, "Usuario": 1}
    })