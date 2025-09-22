from django import forms
from django.db import IntegrityError, models
from django.forms import modelformset_factory
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
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET
from webapp.emails import send_activation_email
from .forms import BilleteraCobroForm, ChequeCobroForm, CuentaBancariaCobroForm, MedioCobroForm, RegistrationForm, LoginForm, TarjetaCobroForm, TipoCobroForm, UserUpdateForm, ClienteForm, AsignarClienteForm, ClienteUpdateForm, TarjetaForm, BilleteraForm, CuentaBancariaForm, ChequeForm, MedioPagoForm, TipoPagoForm, LimiteIntercambioForm
from .decorators import role_required, permitir_permisos
from .utils import get_user_primary_role
from .models import MedioCobro, Role, Currency, Cliente, ClienteUsuario, Categoria, MedioPago, Tarjeta, Billetera, CuentaBancaria, Cheque, TipoCobro, TipoPago, LimiteIntercambio
from django.contrib.auth.decorators import permission_required
from decimal import ROUND_DOWN, Decimal, InvalidOperation

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
    
    # Agregar atributo dinámico "total" a cada moneda
    for currency in currencies:
        currency.totalVenta = float(currency.base_price) + float(currency.comision_venta)
        currency.totalCompra = float(currency.base_price) - float(currency.comision_compra)

    # Obtener la fecha de la última actualización de las monedas
    last_update = None
    if currencies.exists():
        last_update = currencies.order_by('-updated_at').first().updated_at
    
    return render(request, "webapp/home.html", {
        "can_access_gestiones": can_access_gestiones,
        "currencies": currencies,
        "last_update": last_update
    })

@require_GET
def api_active_currencies(request):
        
    # 1. Buscar todas las monedas activas en tu DB
    qs = Currency.objects.filter(is_active=True)

    items = []
    for c in qs:
        # Calcular precio medio en guaraníes
        base = Decimal(c.base_price)
        venta = base + Decimal(c.comision_venta)
        compra = base - Decimal(c.comision_compra)
        mid = (venta + compra) / Decimal("2")

        items.append({
            "code": c.code,                   # USD, EUR, etc.
            "name": c.name,                   # Dólar, Euro
            "decimals": int(c.decimales_monto or 2),
            "pyg_per_unit": float(mid),       # cuánto vale 1 de esa moneda en PYG
        })

    # Asegurar que PYG siempre exista
    if not any(x["code"] == "PYG" for x in items):
        items.append({
            "code": "PYG",
            "name": "Guaraní",
            "decimals": 0,
            "pyg_per_unit": 1.0,
        })

    return JsonResponse({"items": items})

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

# MONEDAS

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
        decimales_cotizacion = request.POST.get('decimales_cotizacion')
        decimales_monto = request.POST.get('decimales_monto')
        flag_image = request.FILES.get('flag_image')
        is_active = request.POST.get('is_active') == "on"

        # Validar que el código no exista
        if Currency.objects.filter(code=code.upper()).exists():
            messages.error(request, 'El código de moneda ya existe.')
            return render(request, 'webapp/create_currency.html')

        # Crear la moneda
        Currency.objects.create(
            code=code.upper(),
            name=name,
            symbol=symbol,
            decimales_cotizacion=decimales_cotizacion,
            decimales_monto=decimales_monto,
            flag_image=flag_image,
            is_active=is_active,
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

        # Validar campos decimales
        try:
            currency.decimales_cotizacion = int(request.POST.get('decimales_cotizacion'))
            currency.decimales_monto = int(request.POST.get('decimales_monto'))
        except (InvalidOperation, ValueError):
            messages.error(request, "Uno de los valores numéricos ingresados no es válido.")
            return render(request, 'webapp/edit_currency.html', {'currency': currency})

        # Checkbox activo
        currency.is_active = bool(request.POST.get('is_active'))

        # Imagen nueva (opcional)
        if request.FILES.get('flag_image'):
            currency.flag_image = request.FILES['flag_image']

        # Guardar
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

# COTIZACIONES

def prices_list(request):
    currencies = Currency.objects.all()
    total = currencies.count()
    activas = currencies.filter(is_active=True).count()
    return render(request, "webapp/prices_list.html", {
        "currencies": currencies,
        "total": total,
        "activas": activas,
    })
@login_required
def edit_prices(request, currency_id):
    currency = get_object_or_404(Currency, id=currency_id)
    
    if request.method == 'POST':

        # Validar campos decimales
        try:
            currency.base_price = Decimal(request.POST.get('base_price').replace(",", "."))
            currency.comision_venta = Decimal(request.POST.get('comision_venta').replace(",", "."))
            currency.comision_compra = Decimal(request.POST.get('comision_compra').replace(",", "."))
            
        except (InvalidOperation, ValueError):
            messages.error(request, "Uno de los valores numéricos ingresados no es válido.")
            return render(request, 'webapp/edit_prices.html', {'currency': currency})


        # Guardar
        currency.save()
        messages.success(request, 'Cotización actualizada exitosamente.')
        return redirect('prices_list')

    return render(request, 'webapp/edit_prices.html', {'currency': currency})


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
    
    return render(request, "webapp/manage_clients.html", context)

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
    
    return render(request, "webapp/modify_client.html", context)

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
    from django.contrib.auth import get_user_model
    from .models import Currency, Cliente
    
    User = get_user_model()
    
    # Obtener métricas reales
    usuarios_activos = User.objects.filter(is_active=True).count()
    monedas_activas = Currency.objects.filter(is_active=True).count()
    clientes_activos = Cliente.objects.filter(estado=True).count()
    
    role = get_user_primary_role(request.user)
    
    context = {
        "role": role,
        "usuarios_activos": usuarios_activos,
        "monedas_activas": monedas_activas,
        "clientes_activos": clientes_activos,
    }
    
    return render(request, "webapp/landing.html", context)

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


# ===========================================
# VISTAS PARA MEDIOS DE PAGO (DEPRECADO)
# ===========================================

@role_required("Administrador")
def manage_client_payment_methods_deprecado(request):
    #Vista para gestionar los medios de pago de los clientes
    # GET - Listar clientes con opción de gestionar medios de pago
    clientes = Cliente.objects.filter(estado=True).order_by('nombre')
    
    return render(request, "webapp/manage_client_payment_methods.html", {
        "clientes": clientes
    })


@role_required("Administrador")
def manage_client_payment_methods_detail_deprecado(request, cliente_id):
    #Vista para gestionar los medios de pago de un cliente específico
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        if request.method == "POST":
            action = request.POST.get("action")
            
            if action == "toggle":
                medio_pago_id = request.POST.get("medio_pago_id")
                try:
                    medio_pago = MedioPago.objects.get(id=medio_pago_id, cliente=cliente)
                    medio_pago.activo = not medio_pago.activo
                    medio_pago.save()
                    status = "activado" if medio_pago.activo else "desactivado"
                    messages.success(request, f"Medio de pago '{medio_pago.nombre}' {status}")
                except MedioPago.DoesNotExist:
                    messages.error(request, "Medio de pago no encontrado")
            
            elif action == "delete":
                medio_pago_id = request.POST.get("medio_pago_id")
                try:
                    medio_pago = MedioPago.objects.get(id=medio_pago_id, cliente=cliente)
                    nombre_medio = medio_pago.nombre
                    medio_pago.delete()
                    messages.success(request, f"Medio de pago '{nombre_medio}' eliminado")
                except MedioPago.DoesNotExist:
                    messages.error(request, "Medio de pago no encontrado")
            
            return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
        
        # GET - Mostrar tipos de medios de pago disponibles y su estado para el cliente
        tipos_disponibles = MedioPago.TIPO_CHOICES
        medios_pago_existentes = MedioPago.objects.filter(cliente=cliente)
        
        # Crear lista de tipos con su estado
        tipos_con_estado = []
        for tipo_codigo, tipo_nombre in tipos_disponibles:
            # Buscar si el cliente tiene medios de pago de este tipo
            medios_del_tipo = medios_pago_existentes.filter(tipo=tipo_codigo)
            
            tipo_info = {
                'codigo': tipo_codigo,
                'nombre': tipo_nombre,
                'tiene_medios': medios_del_tipo.exists(),
                'medios': list(medios_del_tipo),
                'cantidad': medios_del_tipo.count()
            }
            tipos_con_estado.append(tipo_info)
        
        return render(request, "webapp/manage_client_payment_methods_detail.html", {
            "cliente": cliente,
            "tipos_con_estado": tipos_con_estado
        })
        
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("manage_client_payment_methods")


@role_required("Administrador")
def view_client_payment_methods_deprecado(request, cliente_id):
    """Vista para ver los medios de pago de un cliente específico"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        medios_pago = MedioPago.objects.filter(cliente=cliente).order_by('tipo', 'nombre')
        
        return render(request, "webapp/view_client_payment_methods.html", {
            "cliente": cliente,
            "medios_pago": medios_pago
        })
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("manage_client_payment_methods")
 
@role_required("Administrador")
def add_payment_method_deprecado(request, cliente_id, tipo):
    """Vista para agregar un nuevo medio de pago"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        
        if request.method == "POST":
            # Crear el medio de pago base
            medio_pago_form = MedioPagoForm(request.POST)
            
            if medio_pago_form.is_valid():
                medio_pago = medio_pago_form.save(commit=False)
                medio_pago.cliente = cliente
                medio_pago.tipo = tipo
                medio_pago.save()
                
                # Crear el medio de pago específico según el tipo
                if tipo == 'tarjeta':
                    form = TarjetaForm(request.POST)
                elif tipo == 'billetera':
                    form = BilleteraForm(request.POST)
                elif tipo == 'cuenta_bancaria':
                    form = CuentaBancariaForm(request.POST)
                elif tipo == 'cheque':
                    form = ChequeForm(request.POST)
                else:
                    messages.error(request, "Tipo de medio de pago no válido")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
                
                if form.is_valid():
                    medio_especifico = form.save(commit=False)
                    medio_especifico.medio_pago = medio_pago
                    medio_especifico.save()
                    
                    messages.success(request, f"Medio de pago '{medio_pago.nombre}' agregado exitosamente")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
                else:
                    # Si el formulario específico no es válido, eliminar el medio de pago base
                    medio_pago.delete()
            else:
                form = None
        else:
            # GET - Mostrar formularios vacíos
            medio_pago_form = MedioPagoForm()
            if tipo == 'tarjeta':
                form = TarjetaForm()
            elif tipo == 'billetera':
                form = BilleteraForm()
            elif tipo == 'cuenta_bancaria':
                form = CuentaBancariaForm()
            elif tipo == 'cheque':
                form = ChequeForm()
            else:
                messages.error(request, "Tipo de medio de pago no válido")
                return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
        
        return render(request, f"webapp/add_payment_method_{tipo}.html", {
            "cliente": cliente,
            "tipo": tipo,
            "medio_pago_form": medio_pago_form,
            "form": form
        })
        
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("manage_client_payment_methods")


@role_required("Administrador")
def edit_payment_method_deprecado(request, cliente_id, medio_pago_id):
    """Vista para editar un medio de pago existente"""
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        medio_pago = MedioPago.objects.get(id=medio_pago_id, cliente=cliente)
        
        if request.method == "POST":
            # Actualizar el medio de pago base
            medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago)
            
            if medio_pago_form.is_valid():
                medio_pago_form.save()
                
                # Actualizar el medio de pago específico
                if medio_pago.tipo == 'tarjeta':
                    try:
                        medio_especifico = medio_pago.tarjeta
                        form = TarjetaForm(request.POST, instance=medio_especifico)
                    except Tarjeta.DoesNotExist:
                        form = TarjetaForm(request.POST)
                        medio_especifico = None
                elif medio_pago.tipo == 'billetera':
                    try:
                        medio_especifico = medio_pago.billetera
                        form = BilleteraForm(request.POST, instance=medio_especifico)
                    except Billetera.DoesNotExist:
                        form = BilleteraForm(request.POST)
                        medio_especifico = None
                elif medio_pago.tipo == 'cuenta_bancaria':
                    try:
                        medio_especifico = medio_pago.cuenta_bancaria
                        form = CuentaBancariaForm(request.POST, instance=medio_especifico)
                    except CuentaBancaria.DoesNotExist:
                        form = CuentaBancariaForm(request.POST)
                        medio_especifico = None
                elif medio_pago.tipo == 'cheque':
                    try:
                        medio_especifico = medio_pago.cheque
                        form = ChequeForm(request.POST, instance=medio_especifico)
                    except Cheque.DoesNotExist:
                        form = ChequeForm(request.POST)
                        medio_especifico = None
                else:
                    messages.error(request, "Tipo de medio de pago no válido")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
                
                if form.is_valid():
                    if medio_especifico:
                        form.save()
                    else:
                        medio_especifico = form.save(commit=False)
                        medio_especifico.medio_pago = medio_pago
                        medio_especifico.save()
                    
                    messages.success(request, f"Medio de pago '{medio_pago.nombre}' actualizado exitosamente")
                    return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
            else:
                form = None
        else:
            # GET - Mostrar formularios con datos existentes
            medio_pago_form = MedioPagoForm(instance=medio_pago)
            
            if medio_pago.tipo == 'tarjeta':
                try:
                    medio_especifico = medio_pago.tarjeta
                    form = TarjetaForm(instance=medio_especifico)
                except Tarjeta.DoesNotExist:
                    form = TarjetaForm()
            elif medio_pago.tipo == 'billetera':
                try:
                    medio_especifico = medio_pago.billetera
                    form = BilleteraForm(instance=medio_especifico)
                except Billetera.DoesNotExist:
                    form = BilleteraForm()
            elif medio_pago.tipo == 'cuenta_bancaria':
                try:
                    medio_especifico = medio_pago.cuenta_bancaria
                    form = CuentaBancariaForm(instance=medio_especifico)
                except CuentaBancaria.DoesNotExist:
                    form = CuentaBancariaForm()
            elif medio_pago.tipo == 'cheque':
                try:
                    medio_especifico = medio_pago.cheque
                    form = ChequeForm(instance=medio_especifico)
                except Cheque.DoesNotExist:
                    form = ChequeForm()
            else:
                messages.error(request, "Tipo de medio de pago no válido")
                return redirect("manage_client_payment_methods_detail", cliente_id=cliente_id)
        
        return render(request, f"webapp/edit_payment_method_{medio_pago.tipo}.html", {
            "cliente": cliente,
            "medio_pago": medio_pago,
            "medio_pago_form": medio_pago_form,
            "form": form
        })
        
    except (Cliente.DoesNotExist, MedioPago.DoesNotExist):
        messages.error(request, "Cliente o medio de pago no encontrado")
        return redirect("manage_client_payment_methods")

#METODOS DE PAGO (VISTA DE CADA CLIENTE)

FORM_MAP = {
    'tarjeta': TarjetaForm,
    'billetera': BilleteraForm,
    'cuenta_bancaria': CuentaBancariaForm,
    'cheque': ChequeForm
}

@login_required
def my_payment_methods(request):
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medios_pago = MedioPago.objects.filter(cliente=cliente).order_by('tipo', 'nombre')

    # Adjuntar estado global desde TipoPago
    tipos_pago = {tp.nombre.lower(): tp.activo for tp in TipoPago.objects.all()}
    for medio in medios_pago:
        medio.activo_global = tipos_pago.get(medio.tipo, False)

    return render(request, "webapp/my_payment_methods.html", {
        "medios_pago": medios_pago
    })

@login_required
def manage_payment_method(request, tipo, medio_pago_id=None):
    """
    Maneja creación y edición de métodos de pago.
    La moneda solo se puede elegir al crear.
    """
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    FORM_MAP = {
        'tarjeta': TarjetaForm,
        'billetera': BilleteraForm,
        'cuenta_bancaria': CuentaBancariaForm,
        'cheque': ChequeForm
    }
    form_class = FORM_MAP.get(tipo)
    if not form_class:
        raise Http404("Tipo de método de pago desconocido.")

    is_edit = False
    medio_pago = None
    pago_obj = None

    if medio_pago_id:
        medio_pago = get_object_or_404(MedioPago, id=medio_pago_id, cliente=cliente, tipo=tipo)
        pago_obj = getattr(medio_pago, tipo)
        is_edit = True

        if request.GET.get('delete') == "1":
            medio_pago.delete()
            messages.success(request, f"Método de pago '{medio_pago.nombre}' eliminado correctamente")
            return redirect('my_payment_methods')

    if request.method == "POST":
        form = form_class(request.POST, instance=pago_obj)
        medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago)

        if form.is_valid() and medio_pago_form.is_valid():
            if is_edit:
                medio_pago_form.save()
                obj = form.save()
                messages.success(request, f"Método de pago '{medio_pago.nombre}' modificado correctamente")
            else:
                moneda_id = request.POST.get("moneda")
                if not moneda_id:
                    messages.error(request, "Debe seleccionar una moneda")
                    monedas = Currency.objects.filter(is_active=True)
                    return render(request, "webapp/manage_payment_method_base.html", {
                        "tipo": tipo,
                        "form": form,
                        "medio_pago_form": medio_pago_form,
                        "is_edit": is_edit,
                        "monedas": monedas
                    })
                moneda = get_object_or_404(Currency, id=moneda_id)
                mp = MedioPago.objects.create(
                    cliente=cliente,
                    tipo=tipo,
                    nombre=medio_pago_form.cleaned_data['nombre'],
                    moneda=moneda
                )
                obj = form.save(commit=False)
                setattr(obj, "medio_pago", mp)
                obj.save()
                messages.success(request, f"Método de pago '{mp.nombre}' agregado correctamente")

            return redirect('my_payment_methods')
    else:
        form = form_class(instance=pago_obj)
        medio_pago_form = MedioPagoForm(instance=medio_pago)

    monedas = Currency.objects.filter(is_active=True)

    return render(request, "webapp/manage_payment_method_base.html", {
        "tipo": tipo,
        "form": form,
        "medio_pago_form": medio_pago_form,
        "is_edit": is_edit,
        "medio_pago": medio_pago,
        "monedas": monedas
    })


@login_required
def confirm_delete_payment_method(request, medio_pago_id):
    """
    Muestra una página de confirmación antes de eliminar un medio de pago.
    """
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medio_pago = get_object_or_404(MedioPago, id=medio_pago_id, cliente=cliente)
    tipo = medio_pago.tipo

    if request.method == "POST":
        # Eliminar el medio de pago confirmado
        medio_pago.delete()
        messages.success(request, f"Medio de pago '{medio_pago.nombre}' eliminado correctamente")
        return redirect('my_payment_methods')

    return render(request, "webapp/confirm_delete_payment_method.html", {
        "medio_pago": medio_pago,
        "tipo": tipo
    })


# ADMINISTRACION GLOBAL DE METODOS DE PAGO

@login_required
def payment_types_list(request):
    tipos = TipoPago.objects.all().order_by("nombre")
    return render(request, "webapp/payment_types_list.html", {"tipos": tipos})

@login_required
def edit_payment_type(request, tipo_id):
    tipo = get_object_or_404(TipoPago, id=tipo_id)
    if request.method == "POST":
        form = TipoPagoForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect("payment_types_list")
    else:
        form = TipoPagoForm(instance=tipo)
    return render(request, "webapp/edit_payment_type.html", {"form": form, "tipo": tipo})


# ADMINISTRAR LIMITES DE CAMBIO DE MONEDAS POR CATEGORIA DE CLIENTE

@login_required
def limites_intercambio_list(request):
    monedas = Currency.objects.all().order_by('code')
    
    # Obtener todas las categorías dinámicamente
    categorias = Categoria.objects.all().order_by('id')

    tabla = []
    for moneda in monedas:
        fila = {'moneda': moneda, 'limites': {}}
        for categoria in categorias:
            limite, _ = LimiteIntercambio.objects.get_or_create(
                moneda=moneda,
                categoria=categoria,
                defaults={'monto_min': Decimal('0'), 'monto_max': Decimal('0')}
            )
            fila['limites'][categoria.nombre] = {
                'min': limite.monto_min,
                'max': limite.monto_max,
            }
        tabla.append(fila)

    return render(request, 'webapp/limites_intercambio.html', {
        'tabla': tabla,
        'categorias': categorias,
    })


@login_required
def limite_edit(request, moneda_id):
    moneda = get_object_or_404(Currency, id=moneda_id)
    categorias = Categoria.objects.all().order_by('id')

    # Crear límites por defecto si no existen
    limites = {}
    for categoria in categorias:
        limite, _ = LimiteIntercambio.objects.get_or_create(
            moneda=moneda,
            categoria=categoria,
            defaults={'monto_min': 0, 'monto_max': 0}
        )
        limites[categoria.nombre] = limite

    if request.method == "POST":
        dec = moneda.decimales_cotizacion
        errores = False

        for categoria in categorias:
            min_key = f"{categoria.nombre}_min"
            max_key = f"{categoria.nombre}_max"
            try:
                monto_min = Decimal(request.POST.get(min_key)).quantize(
                    Decimal('1.' + '0' * dec), rounding=ROUND_DOWN
                )
                monto_max = Decimal(request.POST.get(max_key)).quantize(
                    Decimal('1.' + '0' * dec), rounding=ROUND_DOWN
                )

                limite = limites[categoria.nombre]
                limite.monto_min = monto_min
                limite.monto_max = monto_max
                limite.save()

            except Exception as e:
                errores = True
                messages.error(request, f"Error en categoría {categoria.nombre}: {e}")

        if not errores:
            messages.success(request, "Límites actualizados correctamente.")
            return redirect("limites_list")

    return render(request, "webapp/limite_edit.html", {
        "moneda": moneda,
        "categorias": categorias,
        "limites": limites,
    })

# ===========================================
# MÉTODOS DE COBRO (VISTA DE CADA CLIENTE)
# ===========================================

FORM_MAP = {
    'tarjeta': TarjetaCobroForm,
    'billetera': BilleteraCobroForm,
    'cuenta_bancaria': CuentaBancariaCobroForm,
    'cheque': ChequeCobroForm
}

@login_required
def my_cobro_methods(request):
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medios_cobro = MedioCobro.objects.filter(cliente=cliente).order_by('tipo', 'nombre')

    # Adjuntar estado global desde TipoPago
    tipos_pago = {tp.nombre.lower(): tp.activo for tp in TipoPago.objects.all()}
    for medio in medios_cobro:
        medio.activo_global = tipos_pago.get(medio.tipo, False)

    return render(request, "webapp/my_cobro_methods.html", {  # Puedes cambiar el template si quieres
        "medios_cobro": medios_cobro
    })


@login_required
def manage_cobro_method(request, tipo, medio_cobro_id=None):
    """
    Maneja creación y edición de métodos de cobro.
    La moneda solo se puede elegir al crear.
    """
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    # Selección del formulario específico según tipo
    FORM_MAP = {
        'tarjeta': TarjetaCobroForm,
        'billetera': BilleteraCobroForm,
        'cuenta_bancaria': CuentaBancariaCobroForm,
        'cheque': ChequeCobroForm
    }
    form_class = FORM_MAP.get(tipo)
    if not form_class:
        raise Http404("Tipo de método de cobro desconocido.")

    is_edit = False
    medio_cobro = None
    cobro_obj = None

    if medio_cobro_id:
        medio_cobro = get_object_or_404(MedioCobro, id=medio_cobro_id, cliente=cliente, tipo=tipo)
        cobro_obj = getattr(medio_cobro, tipo)
        is_edit = True

        if request.GET.get('delete') == "1":
            medio_cobro.delete()
            messages.success(request, f"Método de cobro '{medio_cobro.nombre}' eliminado correctamente")
            return redirect('my_cobro_methods')

    if request.method == "POST":
        form = form_class(request.POST, instance=cobro_obj)
        medio_cobro_form = MedioCobroForm(request.POST, instance=medio_cobro)

        if form.is_valid() and medio_cobro_form.is_valid():
            if is_edit:
                medio_cobro_form.save()
                obj = form.save()
                messages.success(request, f"Método de cobro '{medio_cobro.nombre}' modificado correctamente")
            else:
                # Crear MedioCobro
                moneda_id = request.POST.get("moneda")
                if not moneda_id:
                    messages.error(request, "Debe seleccionar una moneda")
                    monedas = Currency.objects.filter(is_active=True)
                    return render(request, "webapp/manage_cobro_method_base.html", {
                        "tipo": tipo,
                        "form": form,
                        "medio_cobro_form": medio_cobro_form,
                        "is_edit": is_edit,
                        "monedas": monedas
                    })
                moneda = get_object_or_404(Currency, id=moneda_id)
                mp = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo=tipo,
                    nombre=medio_cobro_form.cleaned_data['nombre'],
                    moneda=moneda
                )
                obj = form.save(commit=False)
                setattr(obj, "medio_cobro", mp)
                obj.save()
                messages.success(request, f"Método de cobro '{mp.nombre}' agregado correctamente")

            return redirect('my_cobro_methods')
    else:
        form = form_class(instance=cobro_obj)
        medio_cobro_form = MedioCobroForm(instance=medio_cobro)

    monedas = Currency.objects.filter(is_active=True)

    return render(request, "webapp/manage_cobro_method_base.html", {
        "tipo": tipo,
        "form": form,
        "medio_cobro_form": medio_cobro_form,
        "is_edit": is_edit,
        "medio_cobro": medio_cobro,
        "monedas": monedas
    })



@login_required
def confirm_delete_cobro_method(request, medio_cobro_id):
    """
    Muestra una página de confirmación antes de eliminar un método de cobro.
    """
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medio_cobro = get_object_or_404(MedioCobro, id=medio_cobro_id, cliente=cliente)
    tipo = medio_cobro.tipo

    if request.method == "POST":
        medio_cobro.delete()
        messages.success(request, f"Método de cobro '{medio_cobro.nombre}' eliminado correctamente")
        return redirect('my_cobro_methods')

    return render(request, "webapp/confirm_delete_cobro_method.html", {  # Puedes renombrar template si quieres
        "medio_cobro": medio_cobro,
        "tipo": tipo
    })

@login_required
def cobro_types_list(request):
    tipos = TipoCobro.objects.all().order_by("nombre")
    return render(request, "webapp/cobro_types_list.html", {"tipos": tipos})

@login_required
def edit_cobro_type(request, tipo_id):
    tipo = get_object_or_404(TipoCobro, id=tipo_id)
    if request.method == "POST":
        form = TipoCobroForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect("cobro_types_list")
    else:
        form = TipoCobroForm(instance=tipo)
    return render(request, "webapp/edit_cobro_type.html", {"form": form, "tipo": tipo})

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
