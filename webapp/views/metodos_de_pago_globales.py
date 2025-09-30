from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import TipoPagoForm
from ..decorators import role_required
from ..models import TipoPago

# -----------------------------------------
# ADMINISTRACION GLOBAL DE METODOS DE PAGO (Posibles vistas nuevas)
# -----------------------------------------

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
    
    return render(request, "webapp/metodos_pago_globales/manage_payment_methods.html", context)


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
    
    return render(request, "webapp/metodos_pago_globales/modify_payment_method.html", context)


# -----------------------------------------
# ADMINISTRACION GLOBAL DE METODOS DE PAGO (Posibles vistas viejas)
# -----------------------------------------

@login_required
def payment_types_list(request):
    tipos = TipoPago.objects.all().order_by("nombre")
    return render(request, "webapp/metodos_pago_globales/payment_types_list.html", {"tipos": tipos})

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
    return render(request, "webapp/metodos_pago_globales/edit_payment_type.html", {"form": form, "tipo": tipo})