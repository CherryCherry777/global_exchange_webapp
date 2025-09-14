from django.db import IntegrityError, models
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from webapp.emails import send_activation_email
from .forms import RegistrationForm, LoginForm, UserUpdateForm, ClienteForm, AsignarClienteForm, ClienteUpdateForm
from .decorators import role_required, permitir_permisos
from .utils import get_user_primary_role
from .models import Role, Currency, Cliente, ClienteUsuario, Categoria
from django.contrib.auth.decorators import permission_required


User = get_user_model()
PROTECTED_ROLES = ["Administrador", "Empleado", "Usuario"]
ROLE_TIERS = {
    "Administrador": 3, #numero mayor: mas alto
    "Empleado": 2,
    "Usuario": 1,
}


# -----------------------
# Public / Auth views
# -----------------------
def public_home(request):
    can_access_gestiones = False
    if request.user.is_authenticated:
        user_groups = [g.name for g in request.user.groups.all()]
        if "Administrador" in user_groups or "Analista" in user_groups:
            can_access_gestiones = True
    currencies = Currency.objects.filter(is_active=True)
    return render(request, "webapp/home.html", {
        "can_access_gestiones": can_access_gestiones,
        "currencies": currencies
    })


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # enviar correo real a Mailtrap
            send_activation_email(request, user)

            messages.success(
                request, "Registro Exitoso! Por favor presione su link de verificacion."
            )
            return redirect("login")
        else:
            # Print form errors if invalid
            print("Form errors:", form.errors)
    else:
        form = RegistrationForm()

    return render(request, "webapp/register.html", {"form": form})




def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verificado! Ahora puede hacer login.")
        return redirect("login")
    else:
        messages.error(request, "Link de verificacion expirado o invalido.")
        return redirect("register")

def resend_verification_email(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                send_activation_email(request, user)
                messages.success(request, "Email de verificación reenviado. Por favor revise su correo.")
            else:
                messages.info(request, "Su cuenta ya está activa. Puede hacer login.")
        except User.DoesNotExist:
            messages.error(request, "No se encontró una cuenta con este correo electrónico.")
        return redirect("login")
    
    return render(request, "webapp/resend_verification.html")

# -----------------------
# User Role Management
# -----------------------
# Assign roles to users

def get_highest_role_tier(user):
    user_roles = [g.name for g in user.groups.all()]
    if not user_roles:
        return 0  # No roles
    return min(ROLE_TIERS.get(r, 99) for r in user_roles)

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



# -----------------------
# Role / Permission Management
# -----------------------
@login_required
@role_required("Administrador")
def manage_roles(request):
    roles = Role.objects.select_related("group").all()
    permissions = Permission.objects.all()
    protected_roles = PROTECTED_ROLES
    user_tier = get_highest_role_tier(request.user)

    roles_with_permissions = []
    for role in roles:
        role.available_permissions = permissions.exclude(
            id__in=role.group.permissions.values_list("id", flat=True)
        )
        roles_with_permissions.append(role)

    if request.method == "POST":
        action = request.POST.get("action")
        
        # Solo procesamos acciones que necesitan un role_id
        if action in ["toggle_role", "add_permission", "remove_permission"]:
            role_id = request.POST.get("role_id")
            if not role_id:
                messages.error(request, "No se especificó un rol válido.")
                return redirect("manage_roles")
            
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                messages.error(request, "Rol no encontrado.")
                return redirect("manage_roles")

            role_tier = ROLE_TIERS.get(role.group.name, 0)

            # Check restrictions
            if role.group.name in protected_roles:
                messages.error(request, "No puede modificar este rol.")
                return redirect("manage_roles")
            elif role_tier <= user_tier and role.group.name not in protected_roles:
                # Permitir modificar roles de igual o menor nivel si no son protegidos
                pass

            if action == "toggle_role":
                role.is_active = not role.is_active
                role.save()
                messages.success(
                    request,
                    f"Rol '{role.group.name}' {'activado' if role.is_active else 'desactivado'}."
                )

            elif action == "add_permission":
                perm_id = request.POST.get("permission_id")
                if perm_id:
                    try:
                        perm = Permission.objects.get(id=perm_id)
                        # Acceder al grupo
                        group = role.group
                        # Agregar permiso
                        group.permissions.add(perm)
                        messages.success(request, f"Se agregó '{perm.name}' a '{role.group.name}'.")
                    except Permission.DoesNotExist:
                        messages.error(request, "Permiso no encontrado.")

            elif action == "remove_permission":
                perm_id = request.POST.get("permission_id")
                if perm_id:
                    try:
                        perm = Permission.objects.get(id=perm_id)
                        # Acceder al grupo
                        group = role.group
                        # Agregar permiso
                        group.permissions.remove(perm)
                        messages.success(request, f"Se eliminó '{perm.name}' de '{role.group.name}'.")
                    except Permission.DoesNotExist:
                        messages.error(request, "Permiso no encontrado.")

        return redirect("manage_roles")

    return render(request, "webapp/manage_roles.html", {
        "roles": roles_with_permissions,
        "permissions": permissions,
        "protected_roles": protected_roles,
        "user_tier": user_tier,
    })



@login_required
@role_required("Administrador")
def create_role(request):
    if request.method == "POST":
        roles = Group.objects.all()
        name = request.POST.get("name")
        """
        for rol in roles:
            if name == rol.name:
                messages.error(request, "Ya existe rol con este nombre.")
        """
        if name in PROTECTED_ROLES:
            messages.error(request, "El nombre de este rol esta reservado.")
        else:
            try:
                group = Group.objects.create(name=name)

                # Crear el Role asociado
                Role.objects.create(group=group, is_active=True)
                messages.success(request, f"Role '{name}' created successfully!")
            except IntegrityError:
                messages.error(request, "Ya existe rol con este nombre.")

    return redirect("manage_roles")


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


# -----------------------
# Dashboards
# -----------------------
@role_required("Administrador")
def admin_dash(request):
    return render(request, "webapp/admin_dashboard.html")

@role_required("Empleado")
def employee_dash(request):
    return render(request, "webapp/employee_dashboard.html")


#managing users
@login_required
@role_required("Administrador")
def manage_users(request):
    users = User.objects.all()

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

    return render(request, "webapp/manage_users.html", {"users": users})

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

@login_required
@permission_required('webapp.view_currency', raise_exception=True)
def currency_list(request):
    currencies = Currency.objects.all()
    return render(request, 'webapp/currency_list.html', {'currencies': currencies})

@login_required
def create_currency(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        symbol = request.POST.get('symbol')
        buy_rate = request.POST.get('buy_rate')
        sell_rate = request.POST.get('sell_rate')
        flag_image = request.FILES.get('flag_image')
        decimales_cotizacion = request.POST.get('decimales_cotizacion')
        decimales_monto = request.POST.get('decimales_monto')

        # Validar que el código no exista
        if Currency.objects.filter(code=code).exists():
            messages.error(request, 'El código de moneda ya existe.')
            return render(request, 'webapp/create_currency.html')

        # Crear la moneda
        Currency.objects.create(
            code=code.upper(),
            name=name,
            symbol=symbol,
            buy_rate=buy_rate,
            sell_rate=sell_rate,
            flag_image=flag_image,
            decimales_cotizacion=decimales_cotizacion,
            decimales_monto=decimales_monto
        )
        messages.success(request, 'Moneda creada exitosamente.')
        return redirect('currency_list')

    # GET request - mostrar formulario
    return render(request, 'webapp/create_currency.html')

@login_required
def edit_currency(request, currency_id):
    currency = get_object_or_404(Currency, id=currency_id)
    
    if request.method == 'POST':
        currency.name = request.POST.get('name')
        currency.symbol = request.POST.get('symbol')
        currency.buy_rate = request.POST.get('buy_rate')
        currency.sell_rate = request.POST.get('sell_rate')
        currency.decimales_cotizacion = request.POST.get('decimales_cotizacion')
        currency.decimales_monto = request.POST.get('decimales_monto')
        currency.save()
        messages.success(request, 'Moneda actualizada exitosamente.')
        return redirect('currency_list')
    return render(request, 'webapp/edit_currency.html', {'currency': currency})

@login_required
def toggle_currency(request):
    if request.method == 'POST':
        currency_id = request.POST.get('currency_id')
        currency = get_object_or_404(Currency, id=currency_id)
        
        currency.is_active = not currency.is_active
        currency.save()
        
        status = "activada" if currency.is_active else "desactivada"
        messages.success(request, f'Moneda {status} exitosamente.')
    
    return redirect('currency_list')


# ===========================================
# VISTAS PARA ADMINISTRACIÓN DE CLIENTES
# ===========================================

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
    
    context = {
        'clientes': clientes,
        'search_query': search_query,
        'categoria_filter': categoria_filter,
        'estado_filter': estado_filter,
        'categoria_choices': Cliente._meta.get_field('categoria').choices,
    }
    
    return render(request, "webapp/manage_clientes.html", context)

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
    
    return render(request, "webapp/cliente_form.html", {
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
    
    return render(request, "webapp/cliente_form.html", {
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
    
    return render(request, "webapp/confirm_delete_cliente.html", {'cliente': cliente})

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
    
    return render(request, "webapp/view_cliente.html", context)

class CustomLoginView(LoginView):
    template_name = "webapp/login.html"
    form_class = LoginForm

    def get_success_url(self):
        return reverse_lazy("public_home")
    
    def form_invalid(self, form):
        # Agregar mensaje específico para cuentas inactivas
        if form.errors.get('__all__'):
            for error in form.errors['__all__']:
                if 'inactive' in str(error):
                    messages.error(self.request, str(error))
                    break
        return super().form_invalid(form)

def custom_logout(request):
    logout(request)
    return render(request, "webapp/logout.html")

@login_required
def profile(request):
    return render(request, "webapp/profile.html", {"user": request.user})

@login_required
def edit_profile(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, "webapp/edit_profile.html", {"form": form})

@login_required
def landing_page(request):
    role = get_user_primary_role(request.user)
    return render(request, "webapp/landing.html", {"role": role})

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

# --------------------------------------------
# Vista para asignar clientes a usuarios
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
    
    return render(request, 'webapp/asignar_cliente_usuario.html', {
        'form': form,
        'asignaciones': asignaciones
    })

# --------------------------------------------
# Vista para desasignar cliente de usuario
# --------------------------------------------
@permitir_permisos(['webapp.delete_clienteusuario'])
def desasignar_cliente_usuario(request, asignacion_id):
    asignacion = get_object_or_404(ClienteUsuario, id=asignacion_id)
    cliente_nombre = asignacion.cliente.nombre
    usuario_username = asignacion.usuario.username
    
    asignacion.delete()
    messages.success(request, f"Cliente '{cliente_nombre}' desasignado del usuario '{usuario_username}'.")
    
    return redirect('asignar_cliente_usuario')

# ===========================================
# VISTAS PARA ADMINISTRACIÓN DE CATEGORÍAS
# ===========================================

def manage_categories(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descuento_str = request.POST.get("descuento", "").strip()
        categoria_id = request.POST.get("id")  # Si existe, es edición

        # Validación básica
        try:
            descuento = float(descuento_str)
        except ValueError:
            messages.error(request, "El descuento debe ser un número válido")
            return redirect("manage_categories")

        if not (0 <= descuento <= 1):
            messages.error(request, "El descuento debe estar entre 0 y 1(decimal)")
            return redirect("manage_categories")

        # Validar que tenga máximo un decimal
        partes = str(descuento * 100).split(".")
        if len(partes) > 1 and len(partes[1]) > 1:
            messages.error(request, "El porcentaje solo puede tener un decimal")
            return redirect("manage_categories")

        if categoria_id:  # Editar
            categoria = get_object_or_404(Categoria, pk=categoria_id)
            categoria.nombre = nombre
            categoria.descuento = descuento
            categoria.save()
            messages.success(request, f"Categoría '{categoria.nombre}' actualizada")
        else:  # Crear
            Categoria.objects.create(nombre=nombre, descuento=descuento)
            messages.success(request, f"Categoría '{nombre}' creada")

        return redirect("manage_categories")

    # GET
    categorias = Categoria.objects.all()
    return render(request, "webapp/manage_categories.html", {"categorias": categorias})
