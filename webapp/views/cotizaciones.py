from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.timezone import now, timedelta
from django.db.models import Q
from ..decorators import role_required
from ..models import CurrencyHistory, Transaccion, Currency, CuentaBancaria
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from webapp.emails import send_transaction_cancellation_prompt
from django.contrib.contenttypes.models import ContentType

# ---------------------------------
# Vistas para modificar cotizaciones (Posibles vistas nuevas)
# ---------------------------------

@login_required
@permission_required('webapp.view_currency', raise_exception=True)
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
@permission_required('webapp.change_currency', raise_exception=True)
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
            
            # Avisar sobre los cambios a los usuarios con transacciones pendientes
            promtCancelacionTransaccionCambioCotizacion(request)

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


# Desuscribirse de los correos de tasas
def unsubscribe(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and user.unsubscribe_token == token:
        user.receive_exchange_emails = False
        user.save()
        return redirect('unsubscribe_confirm')
    return redirect('unsubscribe_error')

def unsubscribe_confirm(request):
    """Página que muestra mensaje de confirmación."""
    return render(request, 'webapp/cotizaciones/unsubscribe_confirm.html')


def unsubscribe_error(request):
    """Página que muestra mensaje de error en desuscripción."""
    return render(request, 'webapp/cotizaciones/unsubscribe_error.html')

# -------------------------------------------------------------------------
# Vistas para cancelación de transacción por cambio de tasa
# -------------------------------------------------------------------------

def calcularTasa(transaccion):
    descuentoCategoria = Decimal('0')

    try:
        categoria = transaccion.cliente.categoria
    except Exception:
        categoria = None

    if categoria:
        descuentoCategoria = categoria.descuento or Decimal('0')

    if transaccion.tipo == "VENTA":
        moneda = transaccion.moneda_destino
    else:
        moneda = transaccion.moneda_origen

    # Intentar obtener IDs de método de pago/cobro
    tipo_metodo_pago_id = transaccion.medio_pago
    tipo_metodo_cobro_id = transaccion.medio_cobro

    medio_pago = None
    medio_cobro = None
    if tipo_metodo_pago_id:
        medio_pago = transaccion.medio_pago
    if tipo_metodo_cobro_id:
        medio_cobro = transaccion.medio_cobro


    base = Decimal(moneda.base_price)
    com_venta = Decimal(moneda.comision_venta)
    com_compra = Decimal(moneda.comision_compra)

    # Porcentajes de comisión, seguros
    porc_medio_pago = Decimal('0')
    porc_medio_cobro = Decimal('0')

    if medio_pago and getattr(medio_pago, "tipo_pago", None):
        porc_medio_pago = Decimal(medio_pago.tipo_pago.comision or 0)

    if medio_cobro and getattr(medio_cobro, "tipo_cobro", None):
        porc_medio_cobro = Decimal(medio_cobro.tipo_cobro.comision or 0)

    # Aplicar fórmulas según descuento del cliente
    venta = base + (com_venta * (1 - descuentoCategoria))
    compra = base - (com_compra * (1 - descuentoCategoria))

    # Aplicar comisiones del método seleccionado si existen
    try:
        if porc_medio_cobro and porc_medio_pago:
            # Ajusta la venta y la compra con las comisiones
            venta = venta * (1 + porc_medio_pago/100 + porc_medio_cobro/100)
            compra = compra * (1 - porc_medio_cobro/100 - porc_medio_pago/100)
        elif porc_medio_pago:
            # Solo existe método de pago
            venta = venta * (1 + porc_medio_pago/100)
            compra = compra * (1 - porc_medio_pago/100)
            # compra queda igual o se deja como estaba
        elif porc_medio_cobro:
            # Solo existe método de cobro
            compra = compra * (1 - porc_medio_cobro/100)
            venta = venta * (1 + porc_medio_cobro/100)
            # venta queda igual o se deja como estaba
    except (AttributeError, TypeError, ValueError) as e:
        # Aquí podés decidir qué hacer si algo falla:
        # - loguear el error
        # - usar comisiones 0
        # - dejar venta/compra sin modificar
        print("Error al aplicar comisiones:", e)

    # ✅ Siempre devolver venta/compra sin decimales (PYG siempre)
    venta = venta.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    compra = compra.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    if transaccion.tipo == "VENTA":
        return venta

    return compra


def promtCancelacionTransaccionCambioCotizacion(request, moneda: str | None = None) -> int:
    """
    Recorre transacciones pendientes y, si la tasa actual difiere
    de la tasa almacenada en la transacción, envía un correo al usuario
    preguntando si desea cancelar.

    Devuelve la cantidad de transacciones notificadas.
    """
    ct_cuenta_bancaria = ContentType.objects.get_for_model(CuentaBancaria)

    transacciones = Transaccion.objects.filter(
        estado=Transaccion.Estado.PENDIENTE,
    ).exclude(
        medio_pago_type=ct_cuenta_bancaria
    )

    if moneda:
        transacciones = transacciones.filter(
            Q(moneda_origen__code=moneda) |
            Q(moneda_destino__code=moneda)
        )

    notificados = 0

    for transaccion in transacciones:
        tasa_actual = calcularTasa(transaccion)

        try:
            tasa_antigua = transaccion.tasa_cambio
        except:
            # Si no hay tasa guardada o es inválida, la salteamos
            continue

        if tasa_actual != tasa_antigua:
            send_transaction_cancellation_prompt(
                request,
                transaccion,
                tasa_actual=tasa_actual,
                tasa_antigua=tasa_antigua,
            )
            notificados += 1

    return notificados