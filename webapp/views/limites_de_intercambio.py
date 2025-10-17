from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..models import Currency, LimiteIntercambio
from decimal import ROUND_DOWN, Decimal

# ----------------------------------------------------------
# ADMINISTRAR LIMITES DE CAMBIO DE MONEDAS POR DIA Y POR MES
# ----------------------------------------------------------

# LISTADO DE LÍMITES
@login_required
@permission_required('webapp.view_limiteintercambio', raise_exception=True)
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

    return render(request, 'webapp/limites_intercambio/limites_intercambio.html', {
        'tabla': tabla
    })


# EDITAR LÍMITES
@login_required
@permission_required('webapp.change_limiteintercambio', raise_exception=True)
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

    return render(request, "webapp/limites_intercambio/limite_edit.html", {
        "moneda": moneda,
        "limite": limite
    })
