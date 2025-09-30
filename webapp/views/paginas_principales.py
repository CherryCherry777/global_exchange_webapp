from .constants import *
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import UserUpdateForm
from ..utils import get_user_primary_role
from ..models import Currency, Cliente
from django.contrib.auth import update_session_auth_hash
# -------------
# Public views
# -------------
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

    return render(request, "webapp/paginas_principales/home.html", {
        "can_access_gestiones": can_access_gestiones,
        "currencies": currencies,
        "last_update": last_update,
        "is_guest": is_guest
    })

# ------------------------------
# Vista del selector de clientes
# ------------------------------

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
    from ..context_processors import clientes_disponibles
    clientes_context = clientes_disponibles(request)
    
    return render(request, "webapp/paginas_principales/change_client.html", {
        "clientes_disponibles": clientes_context["clientes_disponibles"]
    })

# ----------------------------
# Vista del perfil del usuario
# ----------------------------

@login_required
def profile(request):
    return render(request, "webapp/paginas_principales/profile.html", {"user": request.user})

@login_required
def edit_profile(request):
    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()
        receive_emails = bool(request.POST.get("receive_exchange_emails"))

        # Validaciones de unicidad
        if username and User.objects.exclude(pk=user.pk).filter(username=username).exists():
            messages.error(request, "El nombre de usuario ya está en uso.")
            return redirect('edit_profile')
        if email and User.objects.exclude(pk=user.pk).filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está en uso.")
            return redirect('edit_profile')

        # Aplicar cambios solo si el campo no está vacío
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if username:
            user.username = username
        if email:
            user.email = email
        # Validación de contraseña
        if password:
            if password != password_confirm:
                messages.error(request, "Las contraseñas no coinciden.")
                return redirect('edit_profile')
            user.set_password(password)
            update_session_auth_hash(request, user)  # Mantener sesión activa

        user.receive_exchange_emails = receive_emails

        user.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect('profile')  # <- ahora sí va a la página de perfil

    return render(request, "webapp/paginas_principales/edit_profile.html", {"user": user})

# ---------------------------------
# Vista del sector de configuración
# ---------------------------------
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
    
    return render(request, "webapp/paginas_principales/landing.html", context)