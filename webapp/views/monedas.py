from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..decorators import role_required
from ..models import Currency
from decimal import InvalidOperation

# -------------------------------
# Vistas de monedas (Posibles vistas nuevas)
# -------------------------------

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


# ----------------
# Currencies CRUD (Posibles vistas viejas)
# ----------------

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