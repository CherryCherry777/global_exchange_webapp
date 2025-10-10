from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from webapp.emails import send_activation_email
from ..forms import BilleteraCobroForm, CuentaBancariaCobroForm, MedioCobroForm
from ..models import MedioCobro, Currency, ClienteUsuario, TipoCobro, TipoPago

# ----------------------------------------
# MÉTODOS DE COBRO (VISTA DE CADA CLIENTE)
# ----------------------------------------

FORM_MAP = {
    #'tarjeta': TarjetaCobroForm,
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

    return render(request, "webapp/metodos_cobro_cliente/my_cobro_methods.html", {
        "medios_cobro": medios_cobro
    })

COBRO_FORM_MAP = {
    #"tarjeta": TarjetaCobroForm,
    "billetera": BilleteraCobroForm,
    "cuenta_bancaria": CuentaBancariaCobroForm,
}


RELATED_MAP = {
    #"tarjeta": "tarjeta_cobro",
    "billetera": "billetera_cobro",
    "cuenta_bancaria": "cuenta_bancaria_cobro",
}

TIPO_COBRO_MAP = {
    'billetera': 'Billetera',
    'cuenta_bancaria': 'Cuenta Bancaria',
    'tauser': 'Tauser'
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
        #'tarjeta': TarjetaCobroForm,
        'billetera': BilleteraCobroForm,
        'cuenta_bancaria': CuentaBancariaCobroForm,
    }

    form_class = cobro_form_map.get(tipo)
    if not form_class:
        raise Http404("Tipo de método de cobro desconocido.")

    # Mapeo de relaciones para acceder al objeto específico
    related_map = {
        #'tarjeta': 'tarjeta_cobro',
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
                    return render(request, "webapp/metodos_cobro_cliente/manage_cobro_method_base.html", {
                        "tipo": tipo,
                        "form": form,
                        "medio_cobro_form": medio_cobro_form,
                        "is_edit": is_edit,
                        "monedas": monedas
                    })
                
                tipo_cobro_nombre = TIPO_COBRO_MAP.get(tipo)
                tipo_cobro = None
                if tipo_cobro_nombre:
                    tipo_cobro = TipoCobro.objects.filter(nombre__iexact=tipo_cobro_nombre).first()

                moneda = get_object_or_404(Currency, id=moneda_id)

                mc = MedioCobro.objects.create(
                    cliente=cliente,
                    tipo=tipo,
                    nombre=medio_cobro_form.cleaned_data['nombre'],
                    moneda=moneda,
                    tipo_cobro=tipo_cobro
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

    return render(request, "webapp/metodos_cobro_cliente/manage_cobro_method_base.html", {
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

    return render(request, "webapp/metodos_cobro_cliente/confirm_delete_cobro_method.html", {
        "medio_cobro": medio_cobro,
        "tipo": tipo
    })
