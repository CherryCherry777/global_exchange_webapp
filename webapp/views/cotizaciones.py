from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.timezone import now, timedelta
from django.db.models import Q
from ..decorators import role_required
from ..models import CurrencyHistory, EmailScheduleConfig, Transaccion, Currency
from decimal import Decimal, InvalidOperation

# ---------------------------------
# Vistas para modificar cotizaciones (Posibles vistas nuevas)
# ---------------------------------

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
    
    return render(request, "webapp/cotizaciones/manage_quotes.html", context)


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
            
            # Cancelar todas las transacciones PENDIENTE donde la moneda esté en origen o destino
            transacciones = Transaccion.objects.filter(
                Q(moneda_origen=currency) | Q(moneda_destino=currency),
                estado=Transaccion.Estado.PENDIENTE
            )

            transacciones.update(estado=Transaccion.Estado.CANCELADA)
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
    
    return render(request, "webapp/cotizaciones/modify_quote.html", context)


# --------------------
# Modify cotizaciones
# --------------------

def prices_list(request):
    currencies = Currency.objects.all()
    total = currencies.count()
    activas = currencies.filter(is_active=True).count()
    return render(request, "webapp/cotizaciones/prices_list.html", {
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
            return render(request, 'webapp/cotizaciones/edit_prices.html', {'currency': currency})


        # Guardar
        currency.save()
        messages.success(request, 'Cotización actualizada exitosamente.')
        return redirect('prices_list')

    return render(request, 'webapp/cotizaciones/edit_prices.html', {'currency': currency})


# ----------------------------------------
# Vistas para el histórico de cotizaciones
# ----------------------------------------

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
    return render(request, "webapp/cotizaciones/historical.html")


# Configuracion de frecuencia de emails de cotizaciones de tasas
def manage_schedule(request):
    config, _ = EmailScheduleConfig.objects.get_or_create(pk=1)

    if request.method == "POST":
        config.frequency = request.POST.get("frequency")
        config.hour = int(request.POST.get("hour", 8))
        config.minute = int(request.POST.get("minute", 0))
        if config.frequency == "custom":
            config.interval_minutes = int(request.POST.get("interval_minutes", 60))
        else:
            config.interval_minutes = None
        config.save()
        return redirect("manage_schedule")

    return render(request, "webapp/cotizaciones/manage_schedule.html", {"config": config})