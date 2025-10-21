from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from webapp.emails import send_activation_email
from ..forms import BilleteraCobroForm, CuentaBancariaCobroForm, MedioCobroForm
from ..models import Cliente, MedioCobro, Currency, ClienteUsuario, TipoCobro, TipoPago

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
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No tiene un cliente seleccionado. Seleccione uno para poder administrar tus métodos de pago, o contacte con un administrador para que le asigne un cliente")
        return redirect("landing")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("landing")

    try: 
        medios_cobro = MedioCobro.objects.filter(cliente=cliente).order_by('tipo', 'nombre')
    except:
        messages.error(request, "No tiene un cliente seleccionado. Seleccione uno para poder administrar tus métodos de pago, o contacte con un administrador para que le asigne un cliente")
        return redirect("landing")


    tipos_cobro = {tp.nombre.lower(): tp.activo for tp in TipoCobro.objects.all()}
    for medio in medios_cobro:
        #medio.activo_global = medio.tipo_pago.activo if medio.tipo_pago else False
        medio.activo_global = medio.activo and (medio.tipo_cobro.activo if medio.tipo_cobro else True)

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
"""
@login_required
def manage_cobro_method(request, tipo, **kwargs):
    
    #Gestiona la creación y edición de los medios de cobro de un cliente:
    #- tarjeta
    #- billetera
    #- cuenta_bancaria
    
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        raise Http404("No tienes un cliente asociado.")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        raise Http404("Cliente no encontrado.")
    
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
"""

@login_required
def manage_cobro_method(request, tipo, **kwargs):
    """
    Crear o editar métodos de cobro de un cliente:
    - billetera
    - cuenta_bancaria
    """

    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No tienes un cliente asociado.")
        return redirect("my_cobro_methods")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect("my_cobro_methods")

    medio_cobro_id = kwargs.get('medio_cobro_id')

    form_class = COBRO_FORM_MAP.get(tipo)
    if not form_class:
        messages.error(request, "Tipo de método de cobro desconocido.")
        return redirect("my_cobro_methods")

    related_field_name = RELATED_MAP.get(tipo)

    # Obtener o crear instancias
    medio_cobro = None
    cobro_obj = None
    is_edit = False

    if medio_cobro_id:
        medio_cobro = get_object_or_404(MedioCobro, id=medio_cobro_id, cliente=cliente, tipo=tipo)
        cobro_obj = getattr(medio_cobro, related_field_name, None)

        # Si no existe la relación, crear instancia vacía (pero sin guardar)
        if cobro_obj is None:
            ModelClass = form_class._meta.model
            cobro_obj = ModelClass(medio_cobro=medio_cobro)

        is_edit = True

        # Manejar eliminación
        if request.GET.get('delete') == "1":
            medio_cobro.delete()
            messages.success(request, f"Método de cobro '{medio_cobro.nombre}' eliminado correctamente")
            return redirect(reverse_lazy('my_cobro_methods'))

    monedas = Currency.objects.filter(is_active=True)

    if request.method == "POST":
        medio_cobro_form = MedioCobroForm(request.POST, instance=medio_cobro)
        cobro_form = form_class(request.POST, instance=cobro_obj)

        if medio_cobro_form.is_valid() and cobro_form.is_valid():
            # Guardar MedioCobro
            medio_cobro_instance = medio_cobro_form.save(commit=False)

            if is_edit:
                # Mantener moneda existente
                medio_cobro_instance.moneda = medio_cobro.moneda
            else:
                # Crear nuevo MedioCobro: asignar cliente, tipo, tipo_cobro y moneda
                medio_cobro_instance.cliente = cliente
                medio_cobro_instance.tipo = tipo

                tipo_cobro_nombre = TIPO_COBRO_MAP.get(tipo)
                if tipo_cobro_nombre:
                    tipo_cobro = TipoCobro.objects.filter(nombre__iexact=tipo_cobro_nombre).first()
                    medio_cobro_instance.tipo_cobro = tipo_cobro

                moneda_id = request.POST.get("moneda")
                if moneda_id:
                    medio_cobro_instance.moneda = get_object_or_404(Currency, id=moneda_id)
                else:
                    medio_cobro_instance.moneda = monedas.first()

            medio_cobro_instance.save()

            # Guardar objeto relacionado
            cobro_instance = cobro_form.save(commit=False)
            cobro_instance.medio_cobro = medio_cobro_instance
            # Mantener moneda sincronizada
            if hasattr(cobro_instance, 'moneda'):
                cobro_instance.moneda = medio_cobro_instance.moneda
            cobro_instance.save()

            msg = "modificado" if is_edit else "agregado"
            messages.success(request, f"Método de cobro '{medio_cobro_instance.nombre}' {msg} correctamente")
            return redirect(reverse_lazy('my_cobro_methods'))
        else:
            # Mostrar errores si no validan
            messages.error(request, "Por favor corrija los errores en el formulario")
            print("MedioCobroForm errors:", medio_cobro_form.errors)
            print(f"{tipo} form errors:", cobro_form.errors)

    else:
        medio_cobro_form = MedioCobroForm(instance=medio_cobro)
        cobro_form = form_class(instance=cobro_obj)

    return render(request, "webapp/metodos_cobro_cliente/manage_cobro_method_base.html", {
        "tipo": tipo,
        "form": cobro_form,
        "medio_cobro_form": medio_cobro_form,
        "is_edit": is_edit,
        "medio_cobro": medio_cobro,
        "monedas": monedas
    })

@login_required
def confirm_delete_cobro_method(request, medio_cobro_id):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No tienes un cliente asociado.")
        return redirect("my_cobro_methods")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect("my_cobro_methods")

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
