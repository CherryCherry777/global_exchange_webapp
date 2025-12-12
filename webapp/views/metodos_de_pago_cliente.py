from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from ..forms import TarjetaNacionalForm, TarjetaInternacionalForm, BilleteraForm, CuentaBancariaForm, MedioPagoForm
from ..models import Currency, MedioPago, TipoPago, TarjetaInternacional, Cliente
from django.conf import settings
import stripe

# -----------------------------------------
# CONFIGURACIÓN STRIPE
# -----------------------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY

# -----------------------------------------
# METODOS DE PAGO (VISTA DE CADA CLIENTE)
# -----------------------------------------

FORM_MAP = {
    'tarjeta_nacional': TarjetaNacionalForm,
    'tarjeta_internacional': TarjetaInternacionalForm,  # Stripe
    'billetera': BilleteraForm,
    'cuenta_bancaria': CuentaBancariaForm,
}

@login_required
def my_payment_methods(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No tiene un cliente seleccionado. Seleccione uno para poder administrar sus métodos de pago, o contacte con un administrador para que le asigne un cliente")
        return redirect("landing")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado")
        return redirect("landing")

    try: 
        medios_pago = MedioPago.objects.filter(cliente=cliente).order_by('tipo', 'nombre')
    except:
        messages.error(request, "No tiene un cliente seleccionado. Seleccione uno para poder administrar sus métodos de pago, o contacte con un administrador para que le asigne un cliente")
        return redirect("landing")

    # Adjuntar estado global desde TipoPago
    tipos_pago = {tp.nombre.lower(): tp.activo for tp in TipoPago.objects.all()}
    for medio in medios_pago:
        medio.activo_global = medio.tipo_pago.activo if medio.tipo_pago else False

    return render(request, "webapp/metodos_pago_cliente/my_payment_methods.html", {
        "medios_pago": medios_pago
    })

"""
@login_required
def manage_payment_method(request, tipo, medio_pago_id=None):
    
    #Maneja creación y edición de métodos de pago.
    #La moneda solo se puede elegir al crear.
    
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        raise Http404("No tienes un cliente asociado.")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        raise Http404("Cliente no encontrado.")

    form_class = FORM_MAP.get(tipo)
    if not form_class:
        raise Http404("Tipo de método de pago desconocido.")

    is_edit = False
    medio_pago = None
    pago_obj = None

    # --- EDICIÓN EXISTENTE ---
    if medio_pago_id:
        medio_pago = get_object_or_404(MedioPago, id=medio_pago_id, cliente=cliente, tipo=tipo)
        pago_obj = getattr(medio_pago, tipo, None)
        is_edit = True

        
        # Si llega ? delete=1
        if request.GET.get('delete') == "1":
            medio_pago.delete()
            messages.success(request, f"Método de pago '{medio_pago.nombre}' eliminado correctamente")
            return redirect('my_payment_methods')
        
            
    if request.method == "POST":
        form = form_class(request.POST, instance=pago_obj)
        medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago, tipo=tipo)

        # Casos especiales: Stripe no usa formulario manual
        if tipo == "tarjeta_internacional":
            if is_edit:
                # Solo permitimos cambiar nombre local
                medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago)
                if medio_pago_form.is_valid():
                    medio_pago_form.save()
                    messages.success(request, f"Nombre del método de pago actualizado correctamente")
                    return redirect("my_payment_methods")
            else:
                # Verificar si el cliente tiene ID en Stripe
                if not cliente.stripe_customer_id:
                    messages.error(request, "El cliente no tiene un ID de Stripe asociado.")
                    return redirect('my_payment_methods')

                # Crear un nuevo PaymentMethod (simulado o por frontend)
                try:
                    # En producción, el frontend envía payment_method_id
                    payment_method_id = request.POST.get("payment_method_id")

                    medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago, tipo=tipo)

                    if not payment_method_id:
                        messages.error(request, "Debe seleccionar una tarjeta válida desde Stripe.")
                        return redirect('my_payment_methods')

                    if not medio_pago_form.is_valid():
                        messages.error(request, "Debe completar el nombre del método de pago.")
                        # Renderiza la misma plantilla con el formulario y errores
                        monedas = Currency.objects.filter(is_active=True)
                        return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
                            "tipo": tipo,
                            "form": form,  # tu otro form
                            "medio_pago_form": medio_pago_form,  # contendrá los errores y los datos ingresados
                            "is_edit": is_edit,
                            "medio_pago": medio_pago,
                            "monedas": monedas,
                            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
                        })
                    
                    # Asociar el método de pago al cliente en Stripe
                    stripe.PaymentMethod.attach(payment_method_id, customer=cliente.stripe_customer_id)

                    # Obtener detalles de la tarjeta
                    pm = stripe.PaymentMethod.retrieve(payment_method_id)
                    card_info = pm.get("card", {})

                    # Nombre que ingresa el usuario en el formulario
                    nombre_input_usuario = medio_pago_form.cleaned_data['nombre']

                    # Marca + últimos 4 dígitos
                    brand = card_info.get("brand").capitalize()

                    # Combinar en un nombre único
                    nombre_medio = f"{nombre_input_usuario} ({brand})"

                    # Crear el MedioPago
                    mp = MedioPago.objects.create(
                        cliente=cliente,
                        tipo="tarjeta_internacional",
                        nombre=nombre_medio,
                    )

                    TarjetaInternacional.objects.create(
                        medio_pago=mp,
                        stripe_payment_method_id=payment_method_id,
                        ultimos_digitos=card_info.get("last4"),
                        exp_month=card_info.get("exp_month"),
                        exp_year=card_info.get("exp_year"),
                    )

                    messages.success(request, "Tarjeta internacional agregada correctamente desde Stripe.")
                    return redirect("my_payment_methods")

                except Exception as e:
                    # Si ocurre un error, eliminar PaymentMethod de Stripe para mantener correlación
                    try:
                        stripe.PaymentMethod.detach(payment_method_id)
                    except Exception as detach_error:
                        # Puedes loguearlo si quieres
                        print(f"No se pudo eliminar el PaymentMethod de Stripe: {detach_error}")

                    messages.error(request, f"Error al registrar la tarjeta: {str(e)}")
                    return redirect("my_payment_methods")

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
                    return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
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

    return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
        "tipo": tipo,
        "form": form,
        "medio_pago_form": medio_pago_form,
        "is_edit": is_edit,
        "medio_pago": medio_pago,
        "monedas": monedas,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY
    })
"""

@login_required
def manage_payment_method(request, tipo, medio_pago_id=None):
    """
    Maneja creación y edición de métodos de pago.
    La moneda solo se puede elegir al crear.
    """
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No tienes un cliente asociado")
        return redirect("my_payment_methods")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect("my_payment_methods")

    form_class = FORM_MAP.get(tipo)
    if not form_class:
        messages.error(request, "Tipo de método de pago desconocido.")
        return redirect("my_payment_methods")

    is_edit = False
    medio_pago = None
    pago_obj = None

    # --- EDICIÓN EXISTENTE ---
    if medio_pago_id:
        medio_pago = get_object_or_404(MedioPago, id=medio_pago_id, cliente=cliente, tipo=tipo)
        pago_obj = getattr(medio_pago, tipo, None)
        is_edit = True

    if request.method == "POST":
        form = form_class(request.POST, instance=pago_obj)
        medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago, tipo=tipo)

        # Casos especiales: Stripe no usa formulario manual
        if tipo == "tarjeta_internacional":
            if is_edit:
                # Solo permitimos cambiar nombre local
                medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago, tipo=tipo)
                if medio_pago_form.is_valid():
                    medio_pago_form.save()
                    messages.success(request, "Nombre del método de pago actualizado correctamente")
                    return redirect("my_payment_methods")
                else:
                    messages.error(request, "Por favor corrija los errores en el formulario")
                    print("MedioPagoForm errors:", medio_pago_form.errors)
                    print(f"{tipo} form errors:", medio_pago.errors)
            else:
                if not cliente.stripe_customer_id:
                    messages.error(request, "El cliente no tiene un ID de Stripe asociado.")
                    return redirect('my_payment_methods')

                try:
                    payment_method_id = request.POST.get("payment_method_id")
                    medio_pago_form = MedioPagoForm(request.POST, instance=medio_pago, tipo=tipo)

                    if not payment_method_id:
                        messages.error(request, "Debe seleccionar una tarjeta válida desde Stripe.")
                        return redirect('my_payment_methods')

                    if not medio_pago_form.is_valid():
                        messages.error(request, "Debe completar el nombre del método de pago.")
                        monedas = Currency.objects.filter(is_active=True)
                        return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
                            "tipo": tipo,
                            "form": form,
                            "medio_pago_form": medio_pago_form,
                            "is_edit": is_edit,
                            "medio_pago": medio_pago,
                            "monedas": monedas,
                            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
                        })
                    
                    stripe.PaymentMethod.attach(payment_method_id, customer=cliente.stripe_customer_id)
                    pm = stripe.PaymentMethod.retrieve(payment_method_id)
                    card_info = pm.get("card", {})

                    nombre_input_usuario = medio_pago_form.cleaned_data['nombre']
                    brand = card_info.get("brand", "").capitalize()
                    nombre_medio = f"{nombre_input_usuario} ({brand})"

                    mp = MedioPago.objects.create(
                        cliente=cliente,
                        tipo="tarjeta_internacional",
                        nombre=nombre_medio,
                    )

                    TarjetaInternacional.objects.create(
                        medio_pago=mp,
                        stripe_payment_method_id=payment_method_id,
                        ultimos_digitos=card_info.get("last4"),
                        exp_month=card_info.get("exp_month"),
                        exp_year=card_info.get("exp_year"),
                    )

                    messages.success(request, "Tarjeta internacional agregada correctamente desde Stripe.")
                    return redirect("my_payment_methods")

                except Exception as e:
                    try:
                        stripe.PaymentMethod.detach(payment_method_id)
                    except Exception as detach_error:
                        print(f"No se pudo eliminar el PaymentMethod de Stripe: {detach_error}")

                    # 2) Extraer mensaje “humano” desde Stripe
                    error_msg = getattr(e, "user_message", None) or str(e)
                    # Opcional: evitar mostrar detalles muy técnicos
                    if ":" in error_msg:
                        error_msg = error_msg.split(":", 1)[-1].strip()

                    # 3) Mostrar mensaje claro al usuario
                    messages.error(request, f"Error al registrar la tarjeta: {error_msg}")

                    # Log real para developer
                    print("Error Stripe (raw):", e)
                    
                    monedas = Currency.objects.filter(is_active=True)
                    return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
                        "tipo": tipo,
                        "form": form,
                        "medio_pago_form": medio_pago_form,
                        "is_edit": is_edit,
                        "medio_pago": medio_pago,
                        "monedas": monedas,
                        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
                    })

        # Validación y guardado normal
        if form.is_valid() and medio_pago_form.is_valid():
            if is_edit:
                medio_pago_form.save()
                form.save()
                messages.success(request, f"Método de pago '{medio_pago.nombre}' modificado correctamente")
            else:
                moneda_id = request.POST.get("moneda")
                if not moneda_id:
                    messages.error(request, "Debe seleccionar una moneda")
                    monedas = Currency.objects.filter(is_active=True)
                    return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
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
            messages.error(request, "Por favor corrija los errores en el formulario")
            print("MedioPagoForm errors:", medio_pago_form.errors)

    else:
        form = form_class(instance=pago_obj)
        medio_pago_form = MedioPagoForm(instance=medio_pago, tipo=tipo)
        if is_edit:
            medio_pago_form.fields['moneda'].disabled = True  # Moneda no editable

    monedas = Currency.objects.filter(is_active=True)

    return render(request, "webapp/metodos_pago_cliente/manage_payment_method_base.html", {
        "tipo": tipo,
        "form": form,
        "medio_pago_form": medio_pago_form,
        "is_edit": is_edit,
        "medio_pago": medio_pago,
        "monedas": monedas,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    })


@login_required
def confirm_delete_payment_method(request, medio_pago_id):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No tienes un cliente asociado.")
        return redirect("my_payment_methods")
    
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Cliente no encontrado.")
        return redirect("my_payment_methods")

    try:
        medio_pago = get_object_or_404(MedioPago, id=medio_pago_id, cliente=cliente)
        tipo = medio_pago.tipo
    except:
        messages.error(request, "No existe ese medio de pago")
        return redirect("my_payment_methods")

    if request.method == "POST":
        try:
            # Si es tarjeta internacional, desasociar en Stripe
            if tipo == "tarjeta_internacional" and hasattr(medio_pago, "tarjeta_internacional"):
                tarjeta = medio_pago.tarjeta_internacional
                stripe.PaymentMethod.detach(tarjeta.stripe_payment_method_id)
                # luego eliminar el registro local
                tarjeta.delete()

            medio_pago.delete()
            messages.success(request, f"Medio de pago '{medio_pago.nombre}' eliminado correctamente")
        except Exception as e:
            messages.error(request, f"No se pudo eliminar el método de pago: {str(e)}")

        return redirect('my_payment_methods')

    return render(request, "webapp/metodos_pago_cliente/confirm_delete_payment_method.html", {
        "medio_pago": medio_pago,
        "tipo": tipo
    })

