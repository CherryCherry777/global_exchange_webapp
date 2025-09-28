from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from ..forms import TarjetaForm, BilleteraForm, CuentaBancariaForm, MedioPagoForm
from ..models import Currency, ClienteUsuario, MedioPago, TipoPago

# -----------------------------------------
# METODOS DE PAGO (VISTA DE CADA CLIENTE)
# -----------------------------------------

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

