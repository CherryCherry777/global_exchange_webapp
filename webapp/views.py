from datetime import timezone
from django import forms
from django.db import IntegrityError, models
from django.forms import modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.utils.timezone import now, timedelta
from django.contrib.contenttypes.models import ContentType
from webapp.emails import send_activation_email
from .forms import BilleteraCobroForm, CuentaBancariaCobroForm, EntidadEditForm, MedioCobroForm, RegistrationForm, LoginForm, TarjetaCobroForm, TipoCobroForm, UserUpdateForm, ClienteForm, AsignarClienteForm, ClienteUpdateForm, TarjetaForm, BilleteraForm, CuentaBancariaForm, MedioPagoForm, TipoPagoForm, LimiteIntercambioForm, EntidadForm, TransaccionForm
from .decorators import role_required, permitir_permisos
from .utils import get_user_primary_role
from .models import CurrencyHistory, Transaccion, Tauser, Entidad, MedioCobro, Role, Currency, Cliente, ClienteUsuario, Categoria, MedioPago, Tarjeta, Billetera, CuentaBancaria, TipoCobro, TipoPago, LimiteIntercambio, TarjetaCobro, CuentaBancariaCobro, BilleteraCobro
from decimal import ROUND_DOWN, Decimal, InvalidOperation
import json

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
    
    is_guest = not request.user.is_authenticated

    return render(request, "webapp/home.html", {
        "can_access_gestiones": can_access_gestiones,
        "currencies": currencies,
        "last_update": last_update,
        "is_guest": is_guest
    })

@require_GET
def api_active_currencies(request):
    user = request.user
    descuento = Decimal('0')  # Por defecto para invitados

    if user.is_authenticated:
        try:
            # Obtener cliente asociado al usuario
            cliente_id = request.session.get("cliente_id")
            cliente_usuario = None
            if cliente_id:
                cliente_usuario = ClienteUsuario.objects.filter(
                    usuario=user,
                    cliente_id=cliente_id
                ).select_related("cliente__categoria").first()
            else:
                descuento = Decimal('0')

            if cliente_usuario and cliente_usuario.cliente.categoria:
                descuento = cliente_usuario.cliente.categoria.descuento or Decimal('0')
        except Exception:
            descuento = Decimal('0')

    # Intentar obtener IDs de método de pago/cobro
    metodo_pago_id = request.GET.get("metodo_pago_id")
    metodo_cobro_id = request.GET.get("metodo_cobro_id")

    metodo_pago = None
    metodo_cobro = None
    if metodo_pago_id:
        try:
            metodo_pago = TipoPago.objects.get(id=metodo_pago_id, activo=True)
        except TipoPago.DoesNotExist:
            metodo_pago = None
    if metodo_cobro_id:
        try:
            metodo_cobro = TipoCobro.objects.get(id=metodo_cobro_id, activo=True)
        except TipoCobro.DoesNotExist:
            metodo_cobro = None

    qs = Currency.objects.filter(is_active=True)
    items = []

    for c in qs:
        base = Decimal(c.base_price)
        com_venta = Decimal(c.comision_venta)
        com_compra = Decimal(c.comision_compra)

        # Aplicar fórmulas según descuento del cliente
        venta = base + (com_venta * (1 - descuento))
        compra = base - (com_compra * (1 - descuento))

        # Aplicar comisiones del método seleccionado si existen
        if metodo_pago:
            venta = venta * (1 + Decimal(metodo_pago.comision)/100 + Decimal(metodo_cobro.comision)/100)
        if metodo_cobro:
            compra = compra * (1 - Decimal(metodo_cobro.comision)/100 - Decimal(metodo_pago.comision)/100)

        items.append({
            "code": c.code,
            "name": c.name,
            "decimals": int(c.decimales_monto or 2),
            "venta": float(venta),
            "compra": float(compra),
        })

    # Asegurar que PYG siempre exista
    if not any(x["code"] == "PYG" for x in items):
        items.append({
            "code": "PYG",
            "name": "Guaraní",
            "decimals": 0,
            "venta": 1.0,
            "compra": 1.0,
        })

    return JsonResponse({"items": items})

@login_required
@require_POST
def set_cliente_seleccionado(request):
    """
    Actualiza la variable de sesión 'cliente_id' según la selección del usuario.
    - Si se recibe un cliente_id válido, se guarda en la sesión.
    - Si no se recibe, se elimina de la sesión (pop).
    Redirige a la página anterior.
    """
    cliente_id = request.POST.get("cliente_id")
    #print(cliente_id)  # Para depuración, imprime el ID seleccionado
    if cliente_id:
        request.session["cliente_id"] = int(cliente_id)
    else:
        request.session.pop('cliente_id', None)  # Borra la sesión si no hay cliente
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def change_client(request):
    """
    Vista para cambiar el cliente seleccionado por el usuario
    """
    if request.method == "POST":
        cliente_id = request.POST.get("cliente_id")
        if cliente_id:
            request.session["cliente_id"] = int(cliente_id)
            messages.success(request, "Cliente seleccionado correctamente.")
        else:
            request.session.pop('cliente_id', None)
            messages.success(request, "Cliente deseleccionado correctamente.")
        
        # Redirigir a la página anterior o al home
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # GET request - mostrar la página de selección
    # Obtener clientes disponibles del context processor
    from .context_processors import clientes_disponibles
    clientes_context = clientes_disponibles(request)
    
    return render(request, "webapp/change_client.html", {
        "clientes_disponibles": clientes_context["clientes_disponibles"]
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

@require_GET
def api_currency_history(request):
    """
    Devuelve histórico de una moneda en JSON.
    Query params:
      - code: código de moneda (ej: USD, EUR)
      - range: week|month|6months|year
    """
    code = request.GET.get("code", "USD")
    rango = request.GET.get("range", "week")

    try:
        currency = Currency.objects.get(code=code)
    except Currency.DoesNotExist:
        return JsonResponse({"error": "Moneda no encontrada"}, status=404)

    today = now().date()
    if rango == "week":
        start = today - timedelta(days=7)
    elif rango == "month":
        start = today - timedelta(days=30)
    elif rango == "6months":
        start = today - timedelta(days=180)
    elif rango == "year":
        start = today - timedelta(days=365)
    else:
        start = today - timedelta(days=30)

    qs = CurrencyHistory.objects.filter(currency=currency, date__gte=start).order_by("date")

    items = [
        {
            "date": h.date.strftime("%d/%m/%Y"),
            "compra": float(h.compra),
            "venta": float(h.venta),
        }
        for h in qs
    ]
    return JsonResponse({"items": items})

@login_required
def historical_view(request):
    return render(request, "webapp/historical.html")

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
    
    return render(request, "webapp/create_client.html", context)

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
                form.save()
                messages.success(request, f"Método de pago '{medio_pago.nombre}' modificado correctamente")
            else:
                moneda_id = request.POST.get("moneda")
                if not moneda_id:
                    messages.error(request, "Debe seleccionar una moneda")
                    monedas = Currency.objects.filter(activo=True)
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
                obj.medio_pago = mp
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
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medio_pago = get_object_or_404(MedioPago, id=medio_pago_id, cliente=cliente)
    tipo = medio_pago.tipo

    if request.method == "POST":
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


# ADMINISTRAR LIMITES DE CAMBIO DE MONEDAS POR DIA Y POR MES

# LISTADO DE LÍMITES
@login_required
def limites_intercambio_list(request):
    monedas = Currency.objects.all().order_by('code')
    tabla = []

    for moneda in monedas:
        limite, _ = LimiteIntercambio.objects.get_or_create(
            moneda=moneda,
            defaults={'limite_dia': 0, 'limite_mes': 0}
        )
        tabla.append({
            'moneda': moneda,
            'limite_dia': limite.limite_dia,
            'limite_mes': limite.limite_mes
        })

    return render(request, 'webapp/limites_intercambio.html', {
        'tabla': tabla
    })


# EDITAR LÍMITES
@login_required
def limite_edit(request, moneda_id):
    moneda = get_object_or_404(Currency, id=moneda_id)
    limite, _ = LimiteIntercambio.objects.get_or_create(
        moneda=moneda,
        defaults={'limite_dia': 0, 'limite_mes': 0}
    )

    if request.method == "POST":
        dec = moneda.decimales_cotizacion
        errores = False
        try:
            limite_dia = Decimal(request.POST.get('limite_dia', 0)).quantize(
                Decimal('1.' + '0' * dec), rounding=ROUND_DOWN
            )
            limite_mes = Decimal(request.POST.get('limite_mes', 0)).quantize(
                Decimal('1.' + '0' * dec), rounding=ROUND_DOWN
            )

            limite.limite_dia = limite_dia
            limite.limite_mes = limite_mes
            limite.save()
        except Exception as e:
            errores = True
            messages.error(request, f"Error al guardar los límites: {e}")

        if not errores:
            messages.success(request, "Límites actualizados correctamente.")
            return redirect("limites_list")

    return render(request, "webapp/limite_edit.html", {
        "moneda": moneda,
        "limite": limite
    })


# ===========================================
# MÉTODOS DE COBRO (VISTA DE CADA CLIENTE)
# ===========================================

FORM_MAP = {
    'tarjeta': TarjetaCobroForm,
    'billetera': BilleteraCobroForm,
    'cuenta_bancaria': CuentaBancariaCobroForm,
}

@login_required
def my_cobro_methods(request):
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medios_cobro = MedioCobro.objects.filter(cliente=cliente).order_by('tipo', 'nombre')

    tipos_pago = {tp.nombre.lower(): tp.activo for tp in TipoPago.objects.all()}
    for medio in medios_cobro:
        medio.activo_global = tipos_pago.get(medio.tipo, False)

    return render(request, "webapp/my_cobro_methods.html", {
        "medios_cobro": medios_cobro
    })

COBRO_FORM_MAP = {
    "tarjeta": TarjetaCobroForm,
    "billetera": BilleteraCobroForm,
    "cuenta_bancaria": CuentaBancariaCobroForm,
}


RELATED_MAP = {
    "tarjeta": "tarjeta_cobro",
    "billetera": "billetera_cobro",
    "cuenta_bancaria": "cuenta_bancaria_cobro",
}

@login_required
def manage_cobro_method(request, tipo, **kwargs):
    """
    Gestiona la creación y edición de los medios de cobro de un cliente:
    - tarjeta
    - billetera
    - cuenta_bancaria
    """
    cliente_usuario = ClienteUsuario.objects.filter(usuario=request.user).first()
    if not cliente_usuario:
        raise Http404("No tienes un cliente asociado.")
    cliente = cliente_usuario.cliente

    medio_cobro_id = kwargs.get('medio_cobro_id')

    # Mapeo de forms por tipo
    cobro_form_map = {
        'tarjeta': TarjetaCobroForm,
        'billetera': BilleteraCobroForm,
        'cuenta_bancaria': CuentaBancariaCobroForm,
    }

    form_class = cobro_form_map.get(tipo)
    if not form_class:
        raise Http404("Tipo de método de cobro desconocido.")

    # Mapeo de relaciones para acceder al objeto específico
    related_map = {
        'tarjeta': 'tarjeta_cobro',
        'billetera': 'billetera_cobro',
        'cuenta_bancaria': 'cuenta_bancaria_cobro',
    }

    is_edit = False
    medio_cobro = None
    cobro_obj = None

    if medio_cobro_id:
        medio_cobro = get_object_or_404(MedioCobro, id=medio_cobro_id, cliente=cliente, tipo=tipo)
        cobro_obj = getattr(medio_cobro, related_map[tipo], None)
        is_edit = True

        # Eliminación desde GET
        if request.GET.get('delete') == "1":
            medio_cobro.delete()
            messages.success(request, f"Método de cobro '{medio_cobro.nombre}' eliminado correctamente")
            return redirect(reverse_lazy('my_cobro_methods'))

    if request.method == "POST":
        form = form_class(request.POST, instance=cobro_obj)
        medio_cobro_form = MedioCobroForm(request.POST, instance=medio_cobro)

        if form.is_valid() and medio_cobro_form.is_valid():
            if is_edit:
                medio_cobro_form.save()
                form.save()
                messages.success(request, f"Método de cobro '{medio_cobro.nombre}' modificado correctamente")
                return redirect('my_cobro_methods')
            else:
                # Crear nuevo medio de cobro
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
                mc = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo=tipo,
                    nombre=medio_cobro_form.cleaned_data['nombre'],
                    moneda=moneda
                )
                obj = form.save(commit=False)
                obj.medio_cobro = mc
                obj.save()
                messages.success(request, f"Método de cobro '{mc.nombre}' agregado correctamente")

            return redirect(reverse_lazy('my_cobro_methods'))
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

    return render(request, "webapp/confirm_delete_cobro_method.html", {
        "medio_cobro": medio_cobro,
        "tipo": tipo
    })

# Administracion de metodos de cobro (Vista de admin)

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

# Administracion de roles

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
    
    return render(request, "webapp/view_client.html", context)


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
    
    return render(request, "webapp/assign_clients.html", context)


@login_required
@role_required("Administrador")
def manage_categories(request):
    """Vista para administrar categorías"""
    # Obtener todas las categorías
    categorias = Categoria.objects.all().order_by('nombre')
    
    # Calcular métricas
    total_categories = Categoria.objects.count()
    
    context = {
        "categorias": categorias,
        "total_categories": total_categories,
    }
    
    return render(request, "webapp/manage_categories.html", context)


@login_required
@role_required("Administrador")
def modify_category(request, category_id):
    """Vista para modificar una categoría"""
    try:
        categoria = Categoria.objects.get(id=category_id)
    except Categoria.DoesNotExist:
        messages.error(request, "Categoría no encontrada.")
        return redirect("manage_categories")
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descuento = request.POST.get("descuento")
        
        try:
            # Validar datos
            if not nombre or not descuento:
                messages.error(request, "Todos los campos son obligatorios.")
                return redirect("modify_category", category_id=category_id)
            
            descuento = Decimal(descuento)
            if descuento < 0 or descuento > 100:
                messages.error(request, "El descuento debe estar entre 0 y 100.")
                return redirect("modify_category", category_id=category_id)
            
            # Validar máximo 1 decimal
            if descuento.as_tuple().exponent < -1:  # ej: -2 sería 2 decimales
                messages.error(request, "El descuento solo puede tener como máximo 1 decimal (ej: 10.5, no 10.55).")
                return redirect("modify_category", category_id=category_id)
            
            # Actualizar categoría
            categoria.nombre = nombre
            categoria.descuento = descuento / 100
            categoria.save()
            
            messages.success(request, f"Categoría '{categoria.nombre}' actualizada correctamente.")
            return redirect("manage_categories")
            
        except ValueError:
            messages.error(request, "El descuento debe ser un número válido.")
            return redirect("modify_category", category_id=category_id)
        except Exception as e:
            messages.error(request, "Error al actualizar la categoría.")
            return redirect("modify_category", category_id=category_id)
    
    context = {
        "categoria": categoria,
    }
    
    return render(request, "webapp/modify_category.html", context)


@login_required
@role_required("Administrador")
def manage_currencies(request):
    """Vista para administrar monedas"""
    currencies = Currency.objects.all().order_by('name')
    total_currencies = currencies.count()
    active_currencies = currencies.filter(is_active=True).count()
    
    if request.method == "POST":
        action = request.POST.get("action")
        currency_id = request.POST.get("currency_id")
        
        try:
            currency = Currency.objects.get(id=currency_id)
            
            if action == "activate":
                currency.is_active = True
                currency.save()
                messages.success(request, f"Moneda '{currency.name}' activada correctamente.")
            elif action == "deactivate":
                currency.is_active = False
                currency.save()
                messages.success(request, f"Moneda '{currency.name}' desactivada correctamente.")
            else:
                messages.error(request, "Acción no válida.")
                
        except Currency.DoesNotExist:
            messages.error(request, "Moneda no encontrada.")
        except Exception as e:
            messages.error(request, "Error al procesar la solicitud.")
    
    context = {
        "currencies": currencies,
        "total_currencies": total_currencies,
        "active_currencies": active_currencies,
    }
    
    return render(request, "webapp/manage_currencies.html", context)


@login_required
@role_required("Administrador")
def create_currency(request):
    """Vista para crear una nueva moneda"""
    if request.method == "POST":
        code = request.POST.get("code")
        name = request.POST.get("name")
        symbol = request.POST.get("symbol")
        decimales_cotizacion = request.POST.get("decimales_cotizacion")
        decimales_monto = request.POST.get("decimales_monto")
        is_active = request.POST.get("is_active") == "on"
        flag_image = request.FILES.get("flag_image")
        
        try:
            # Validar datos
            if not all([code, name, symbol, decimales_cotizacion, decimales_monto]):
                messages.error(request, "Todos los campos obligatorios deben ser completados.")
                return redirect("create_currency")
            
            # Validar código único
            if Currency.objects.filter(code=code.upper()).exists():
                messages.error(request, f"Ya existe una moneda con el código '{code.upper()}'.")
                return redirect("create_currency")
            
            # Validar decimales
            decimales_cotizacion = int(decimales_cotizacion)
            decimales_monto = int(decimales_monto)
            
            if not (0 <= decimales_cotizacion <= 8):
                messages.error(request, "Los decimales de cotización deben estar entre 0 y 8.")
                return redirect("create_currency")
            
            if not (0 <= decimales_monto <= 8):
                messages.error(request, "Los decimales de monto deben estar entre 0 y 8.")
                return redirect("create_currency")
            
            # Crear moneda
            currency = Currency.objects.create(
                code=code.upper(),
                name=name,
                symbol=symbol,
                decimales_cotizacion=decimales_cotizacion,
                decimales_monto=decimales_monto,
                is_active=is_active,
                flag_image=flag_image
            )
            
            messages.success(request, f"Moneda '{currency.name}' creada correctamente.")
            return redirect("manage_currencies")
            
        except ValueError:
            messages.error(request, "Los valores de decimales deben ser números válidos.")
            return redirect("create_currency")
        except Exception as e:
            messages.error(request, "Error al crear la moneda.")
            return redirect("create_currency")
    
    return render(request, "webapp/create_currency.html")


@login_required
@role_required("Administrador")
def modify_currency(request, currency_id):
    """Vista para modificar una moneda"""
    try:
        currency = Currency.objects.get(id=currency_id)
    except Currency.DoesNotExist:
        messages.error(request, "Moneda no encontrada.")
        return redirect("manage_currencies")
    
    if request.method == "POST":
        name = request.POST.get("name")
        symbol = request.POST.get("symbol")
        decimales_cotizacion = request.POST.get("decimales_cotizacion")
        decimales_monto = request.POST.get("decimales_monto")
        is_active = request.POST.get("is_active") == "on"
        flag_image = request.FILES.get("flag_image")
        
        try:
            # Validar datos
            if not all([name, symbol, decimales_cotizacion, decimales_monto]):
                messages.error(request, "Todos los campos obligatorios deben ser completados.")
                return redirect("modify_currency", currency_id=currency_id)
            
            # Validar decimales
            decimales_cotizacion = int(decimales_cotizacion)
            decimales_monto = int(decimales_monto)
            
            if not (0 <= decimales_cotizacion <= 8):
                messages.error(request, "Los decimales de cotización deben estar entre 0 y 8.")
                return redirect("modify_currency", currency_id=currency_id)
            
            if not (0 <= decimales_monto <= 8):
                messages.error(request, "Los decimales de monto deben estar entre 0 y 8.")
                return redirect("modify_currency", currency_id=currency_id)
            
            # Actualizar moneda
            currency.name = name
            currency.symbol = symbol
            currency.decimales_cotizacion = decimales_cotizacion
            currency.decimales_monto = decimales_monto
            currency.is_active = is_active
            
            # Actualizar bandera solo si se proporciona una nueva
            if flag_image:
                currency.flag_image = flag_image
            
            currency.save()
            
            messages.success(request, f"Moneda '{currency.name}' actualizada correctamente.")
            return redirect("manage_currencies")
            
        except ValueError:
            messages.error(request, "Los valores de decimales deben ser números válidos.")
            return redirect("modify_currency", currency_id=currency_id)
        except Exception as e:
            messages.error(request, "Error al actualizar la moneda.")
            return redirect("modify_currency", currency_id=currency_id)
    
    context = {
        "currency": currency,
    }
    
    return render(request, "webapp/modify_currency.html", context)


@login_required
@role_required("Administrador")
def manage_quotes(request):
    """Vista para administrar cotizaciones"""
    currencies = Currency.objects.all().order_by('name')
    total_quotes = currencies.count()
    active_quotes = currencies.filter(is_active=True).count()
    
    if request.method == "POST":
        action = request.POST.get("action")
        currency_id = request.POST.get("currency_id")
        
        try:
            currency = Currency.objects.get(id=currency_id)
            
            if action == "activate":
                currency.is_active = True
                currency.save()
                messages.success(request, f"Cotización de '{currency.name}' activada correctamente.")
            elif action == "deactivate":
                currency.is_active = False
                currency.save()
                messages.success(request, f"Cotización de '{currency.name}' desactivada correctamente.")
            else:
                messages.error(request, "Acción no válida.")
                
        except Currency.DoesNotExist:
            messages.error(request, "Moneda no encontrada.")
        except Exception as e:
            messages.error(request, "Error al procesar la solicitud.")
    
    context = {
        "currencies": currencies,
        "total_quotes": total_quotes,
        "active_quotes": active_quotes,
    }
    
    return render(request, "webapp/manage_quotes.html", context)


@login_required
@role_required("Administrador")
def modify_quote(request, currency_id):
    """Vista para modificar una cotización"""
    try:
        currency = Currency.objects.get(id=currency_id)
    except Currency.DoesNotExist:
        messages.error(request, "Moneda no encontrada.")
        return redirect("manage_quotes")
    
    if request.method == "POST":
        base_price = request.POST.get("base_price")
        comision_compra = request.POST.get("comision_compra")
        comision_venta = request.POST.get("comision_venta")
        is_active = request.POST.get("is_active") == "on"
        
        try:
            # Validar datos
            if not all([base_price, comision_compra, comision_venta]):
                messages.error(request, "Todos los campos obligatorios deben ser completados.")
                return redirect("modify_quote", currency_id=currency_id)
            
            # Validar valores numéricos
            base_price = float(base_price)
            comision_compra = float(comision_compra)
            comision_venta = float(comision_venta)
            
            if base_price < 0 or comision_compra < 0 or comision_venta < 0:
                messages.error(request, "Los valores no pueden ser negativos.")
                return redirect("modify_quote", currency_id=currency_id)
            
            # Actualizar cotización
            currency.base_price = base_price
            currency.comision_compra = comision_compra
            currency.comision_venta = comision_venta
            currency.is_active = is_active
            currency.save()
            
            messages.success(request, f"Cotización de '{currency.name}' actualizada correctamente.")
            return redirect("manage_quotes")
            
        except ValueError:
            messages.error(request, "Los valores deben ser números válidos.")
            return redirect("modify_quote", currency_id=currency_id)
        except Exception as e:
            messages.error(request, "Error al actualizar la cotización.")
            return redirect("modify_quote", currency_id=currency_id)
    
    # Asegurar que los valores tengan valores por defecto si están vacíos
    if not currency.base_price:
        currency.base_price = 1.0
    if not currency.comision_compra:
        currency.comision_compra = 1.0
    if not currency.comision_venta:
        currency.comision_venta = 1.0
    
    context = {
        "currency": currency,
    }
    
    return render(request, "webapp/modify_quote.html", context)


@login_required
@role_required("Administrador")
def manage_payment_methods(request):
    """
    Vista para administrar métodos de pago globales
    """
    
    # Obtener todos los métodos de pago (TipoPago)
    payment_methods = TipoPago.objects.all().order_by('nombre')
    total_payment_methods = payment_methods.count()
    
    context = {
        "payment_methods": payment_methods,
        "total_payment_methods": total_payment_methods,
    }
    
    return render(request, "webapp/manage_payment_methods.html", context)


@login_required
@role_required("Administrador")
def modify_payment_method(request, payment_method_id):
    """
    Vista para modificar un método de pago global
    """
    try:
        payment_method = TipoPago.objects.get(id=payment_method_id)
    except TipoPago.DoesNotExist:
        messages.error(request, "El método de pago no existe.")
        return redirect("manage_payment_methods")
    
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            comision = request.POST.get("comision")
            activo = request.POST.get("activo") == "on"
            
            # Validar datos
            if not comision:
                messages.error(request, "La comisión es requerida.")
                return redirect("modify_payment_method", payment_method_id=payment_method_id)
            
            try:
                comision_decimal = float(comision)
                if comision_decimal < 0 or comision_decimal > 100:
                    messages.error(request, "La comisión debe estar entre 0 y 100.")
                    return redirect("modify_payment_method", payment_method_id=payment_method_id)
            except ValueError:
                messages.error(request, "La comisión debe ser un número válido.")
                return redirect("modify_payment_method", payment_method_id=payment_method_id)
            
            # Actualizar el método de pago
            payment_method.comision = comision_decimal
            payment_method.activo = activo
            payment_method.save()
            
            messages.success(request, f"El método de pago '{payment_method.nombre}' ha sido actualizado exitosamente.")
            return redirect("manage_payment_methods")
            
        except Exception as e:
            messages.error(request, "Error al actualizar el método de pago.")
            return redirect("modify_payment_method", payment_method_id=payment_method_id)
    
    context = {
        "payment_method": payment_method,
    }
    
    return render(request, "webapp/modify_payment_method.html", context)


@login_required
@role_required("Administrador")
def manage_cobro_methods(request):
    """
    Vista para administrar métodos de cobro globales
    """
    # Obtener todos los métodos de cobro (TipoCobro)
    cobro_methods = TipoCobro.objects.all().order_by('nombre')
    total_cobro_methods = cobro_methods.count()
    
    context = {
        "cobro_methods": cobro_methods,
        "total_cobro_methods": total_cobro_methods,
    }
    
    return render(request, "webapp/manage_cobro_methods.html", context)


@login_required
@role_required("Administrador")
def modify_cobro_method(request, cobro_method_id):
    """
    Vista para modificar un método de cobro global
    """
    try:
        cobro_method = TipoCobro.objects.get(id=cobro_method_id)
    except TipoCobro.DoesNotExist:
        messages.error(request, "El método de cobro no existe.")
        return redirect("manage_cobro_methods")
    
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            comision = request.POST.get("comision")
            activo = request.POST.get("activo") == "on"
            
            # Validar datos
            if not comision:
                messages.error(request, "La comisión es requerida.")
                return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
            
            try:
                comision_decimal = float(comision)
                if comision_decimal < 0 or comision_decimal > 100:
                    messages.error(request, "La comisión debe estar entre 0 y 100.")
                    return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
            except ValueError:
                messages.error(request, "La comisión debe ser un número válido.")
                return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
            
            # Actualizar el método de cobro
            cobro_method.comision = comision_decimal
            cobro_method.activo = activo
            cobro_method.save()
            
            messages.success(request, f"El método de cobro '{cobro_method.nombre}' ha sido actualizado exitosamente.")
            return redirect("manage_cobro_methods")
            
        except Exception as e:
            messages.error(request, "Error al actualizar el método de cobro.")
            return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
    
    context = {
        "cobro_method": cobro_method,
    }
    
    return render(request, "webapp/modify_cobro_method.html", context)

# ===========================================
# Vistas de compraventa
# ===========================================

def compraventa_view(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        # Agregar mensaje de error
        messages.error(request, "No hay cliente seleccionado")
        # Redirigir a la página change_client.html
        return redirect("change_client") 

    cliente = get_object_or_404(Cliente, id=cliente_id)

    if request.method == "POST":
        # Confirmación final
        if "confirmar" in request.POST:
            data = request.session.get("form_data")
            if not data:
                return redirect("compraventa")

            # Construcción de transacción
            transaccion = Transaccion(
                cliente=cliente,
                usuario=request.user,
                tipo=data["tipo"],
                moneda_origen=Currency.objects.get(code=data["moneda_origen"]),
                moneda_destino=Currency.objects.get(code=data["moneda_destino"]),
                tasa_cambio=data["tasa_cambio"],
                monto_origen=data["monto_origen"],
                monto_destino=data["monto_destino"],
                medio_pago_type=ContentType.objects.get_for_id(data["medio_pago_type"]),
                medio_pago_id=data["medio_pago_id"],
                medio_cobro_type=ContentType.objects.get_for_id(data["medio_cobro_type"]),
                medio_cobro_id=data["medio_cobro_id"],
            )
            transaccion.save()

            # limpiar la sesión
            request.session.pop("form_data", None)
            return redirect("transaccion_list")

        # Paso previo: guardar en sesión y mostrar confirmación
        data = {
            "tipo": request.POST.get("tipo"),
            "moneda_origen": request.POST.get("moneda_origen"),
            "moneda_destino": request.POST.get("moneda_destino"),
            "tasa_cambio": request.POST.get("tasa_cambio"),
            "monto_origen": request.POST.get("monto_origen"),
            "monto_destino": request.POST.get("monto_destino"),
            "medio_pago_type": request.POST.get("medio_pago_type"),
            "medio_pago_id": request.POST.get("medio_pago_id"),
            "medio_cobro_type": request.POST.get("medio_cobro_type"),
            "medio_cobro_id": request.POST.get("medio_cobro_id"),
        }

        request.session["form_data"] = data
        return render(request, "webapp/confirmation_compraventa.html", {"data": data})

    return render(request, "webapp/compraventa.html")

def get_metodos_pago_cobro(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"metodo_pago": [], "metodo_cobro": []})

    moneda_pago = request.GET.get("from")
    moneda_cobro = request.GET.get("to")

    print(moneda_pago)
    print(moneda_cobro)
    # ---------------- ContentTypes ----------------
    ct_tarjeta = ContentType.objects.get_for_model(Tarjeta)
    ct_transferencia = ContentType.objects.get_for_model(CuentaBancaria)
    ct_billetera = ContentType.objects.get_for_model(Billetera)
    ct_tauser = ContentType.objects.get_for_model(Tauser)

    ct_tarjeta_cobro = ContentType.objects.get_for_model(TarjetaCobro)
    ct_transferencia_cobro = ContentType.objects.get_for_model(CuentaBancariaCobro)
    ct_billetera_cobro = ContentType.objects.get_for_model(BilleteraCobro)

    # ---------------- Métodos de Pago ----------------
    metodo_pago = []

    tarjetas = Tarjeta.objects.filter(
        medio_pago__cliente__id=cliente_id, medio_pago__activo=True
    ).select_related("medio_pago__tipo_pago", "entidad")
    for t in tarjetas:
        if moneda_pago and t.medio_pago.moneda.code != moneda_pago:
            continue
        metodo_pago.append({
            "id": t.id,
            "tipo": "tarjeta",
            "nombre": f"Tarjeta ****{t.ultimos_digitos}",
            "tipo_general_id": t.medio_pago.tipo_pago_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "content_type_id": ct_tarjeta.id,
            "moneda_code": t.medio_pago.moneda.code
        })

    transferencias = CuentaBancaria.objects.filter(
        medio_pago__cliente__id=cliente_id, medio_pago__activo=True
    ).select_related("medio_pago__tipo_pago", "entidad")
    for t in transferencias:
        if moneda_pago and t.medio_pago.moneda.code != moneda_pago:
            continue
        metodo_pago.append({
            "id": t.id,
            "tipo": "transferencia",
            "nombre": f"Transferencia {t.entidad.nombre}" if t.entidad else "Transferencia",
            "numero_cuenta": t.numero_cuenta,
            "tipo_general_id": t.medio_pago.tipo_pago_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_pago.moneda.code,
            "content_type_id": ct_transferencia.id
        })

    billeteras = Billetera.objects.filter(
        medio_pago__cliente__id=cliente_id, medio_pago__activo=True
    ).select_related("medio_pago__tipo_pago", "entidad")
    for t in billeteras:
        if moneda_pago and t.medio_pago.moneda.code != moneda_pago:
            continue
        metodo_pago.append({
            "id": t.id,
            "tipo": "billetera",
            "nombre": f"Billetera {t.entidad.nombre}" if t.entidad else "Billetera",
            "tipo_general_id": t.medio_pago.tipo_pago_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_pago.moneda.code,
            "content_type_id": ct_billetera.id
        })

    tausers = Tauser.objects.filter(activo=True)
    for t in tausers:
        metodo_pago.append({
            "id": t.id,
            "tipo": t.tipo,
            "nombre": t.nombre,
            "ubicacion": t.ubicacion,
            "tipo_general_id": t.tipo_pago_id,
            "moneda_code": None,
            "content_type_id": ct_tauser.id
        })

    # ---------------- Métodos de Cobro ----------------
    metodo_cobro = []

    tarjetas = TarjetaCobro.objects.filter(
        medio_cobro__cliente__id=cliente_id, medio_cobro__activo=True
    ).select_related("medio_cobro__tipo_cobro", "entidad")
    for t in tarjetas:
        if moneda_cobro and t.medio_cobro.moneda.code != moneda_cobro:
            continue
        metodo_cobro.append({
            "id": t.id,
            "tipo": "tarjeta",
            "nombre": f"Tarjeta ****{t.ultimos_digitos}",
            "tipo_general_id": t.medio_cobro.tipo_cobro_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_cobro.moneda.code,
            "content_type_id": ct_tarjeta_cobro.id
        })

    transferencias = CuentaBancariaCobro.objects.filter(
        medio_cobro__cliente__id=cliente_id, medio_cobro__activo=True
    ).select_related("medio_cobro__tipo_cobro", "entidad")
    for t in transferencias:
        if moneda_cobro and t.medio_cobro.moneda.code != moneda_cobro:
            continue
        metodo_cobro.append({
            "id": t.id,
            "tipo": "transferencia",
            "nombre": f"Transferencia {t.entidad.nombre}" if t.entidad else "Transferencia",
            "numero_cuenta": t.numero_cuenta,
            "tipo_general_id": t.medio_cobro.tipo_cobro_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_cobro.moneda.code,
            "content_type_id": ct_transferencia_cobro.id
        })

    billeteras = BilleteraCobro.objects.filter(
        medio_cobro__cliente__id=cliente_id, medio_cobro__activo=True
    ).select_related("medio_cobro__tipo_cobro", "entidad")
    for t in billeteras:
        if moneda_cobro and t.medio_cobro.moneda.code != moneda_cobro:
            continue
        metodo_cobro.append({
            "id": t.id,
            "tipo": "billetera",
            "nombre": f"Billetera {t.entidad.nombre}" if t.entidad else "Billetera",
            "tipo_general_id": t.medio_cobro.tipo_cobro_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_cobro.moneda.code,
            "content_type_id": ct_billetera_cobro.id
        })

    tausers = Tauser.objects.filter(activo=True)
    for t in tausers:
        metodo_cobro.append({
            "id": t.id,
            "tipo": t.tipo,
            "nombre": t.nombre,
            "ubicacion": t.ubicacion,
            "tipo_general_id": t.tipo_cobro_id,
            "moneda_code": None,
            "content_type_id": ct_tauser.id
        })

    return JsonResponse({"metodo_pago": metodo_pago, "metodo_cobro": metodo_cobro})

def transaccion_list(request):
    transacciones = Transaccion.objects.select_related(
        "cliente", "usuario", "moneda_origen", "moneda_destino", "factura_asociada"
    ).all()
    return render(request, "webapp/historial_transacciones.html", {"transacciones": transacciones})

# ENTIDADES BANCARIAS Y TELEFONICAS PARA MEDIOS DE PAGO O COBRO
@login_required
def entidad_list(request):
    entidades = Entidad.objects.all().order_by("nombre")
    return render(request, "webapp/entidad_list.html", {"entidades": entidades})


@login_required
def entidad_create(request):
    if request.method == "POST":
        form = EntidadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Entidad creada correctamente")
            return redirect("entidad_list")
    else:
        form = EntidadForm()

    return render(request, "webapp/entidad_form.html", {"form": form})


@login_required
def entidad_update(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)

    if request.method == "POST":
        form = EntidadEditForm(request.POST, instance=entidad)
        if form.is_valid():
            form.save()
            messages.success(request, "Entidad actualizada correctamente")
            return redirect("entidad_list")
    else:
        form = EntidadEditForm(instance=entidad)

    return render(request, "webapp/entidad_form.html", {"form": form, "entidad": entidad})


@login_required
def entidad_toggle(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)
    entidad.activo = not entidad.activo
    entidad.save()
    messages.success(request, f"Entidad '{entidad.nombre}' actualizada correctamente")
    return redirect("entidad_list")


