from webapp.views.cotizaciones import promtCancelacionTransaccionCambioCotizacion
from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from ..forms import TipoCobroForm
from ..decorators import role_required
from ..models import TipoCobro

# ----------------------------------------
# MÉTODOS DE COBRO (VISTA DE ADMIN) (Posibles vistas nuevas)
# ----------------------------------------

@login_required
@permission_required('webapp.view_mediocobro', raise_exception=True)
def manage_cobro_methods(request):
    """
    Vista para administrar métodos de cobro globales
    """
    # Obtener todos los métodos de cobro (TipoCobro)
    cobro_methods = TipoCobro.objects.all().order_by('nombre')
    total_cobro_methods = cobro_methods.count()
    
    context = {
        "cobro_methods": cobro_methods,
        "total_cobro_methods": total_cobro_methods,
    }
    
    return render(request, "webapp/metodos_cobro_globales/manage_cobro_methods.html", context)


@login_required
@permission_required('webapp.view_mediocobro', raise_exception=True)
def modify_cobro_method(request, cobro_method_id):
    """
    Vista para modificar un método de cobro global
    """
    try:
        cobro_method = TipoCobro.objects.get(id=cobro_method_id)
    except TipoCobro.DoesNotExist:
        messages.error(request, "El método de cobro no existe.")
        return redirect("manage_cobro_methods")
    
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            comision = request.POST.get("comision")
            activo = request.POST.get("activo") == "on"
            
            # Validar datos
            if not comision:
                messages.error(request, "La comisión es requerida.")
                return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
            
            try:
                comision_decimal = float(comision)
                if comision_decimal < 0 or comision_decimal > 100:
                    messages.error(request, "La comisión debe estar entre 0 y 100.")
                    return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
            except ValueError:
                messages.error(request, "La comisión debe ser un número válido.")
                return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
            
            # Actualizar el método de cobro
            cobro_method.comision = comision_decimal
            cobro_method.activo = activo
            cobro_method.save()

            # Avisar de actualizaciones en transacciones pendientes
            promtCancelacionTransaccionCambioCotizacion()
            
            messages.success(request, f"El método de cobro '{cobro_method.nombre}' ha sido actualizado exitosamente.")
            return redirect("manage_cobro_methods")
            
        except Exception as e:
            messages.error(request, "Error al actualizar el método de cobro.")
            return redirect("modify_cobro_method", cobro_method_id=cobro_method_id)
    
    context = {
        "cobro_method": cobro_method,
    }
    
    return render(request, "webapp/metodos_cobro_globales/modify_cobro_method.html", context)


# ----------------------------------------
# MÉTODOS DE COBRO (VISTA DE ADMIN) (Posibles vistas viejas)
# ----------------------------------------

@login_required
def cobro_types_list(request):
    tipos = TipoCobro.objects.all().order_by("nombre")
    return render(request, "webapp/metodos_cobro_globales/cobro_types_list.html", {"tipos": tipos})

@login_required
def edit_cobro_type(request, tipo_id):
    tipo = get_object_or_404(TipoCobro, id=tipo_id)
    if request.method == "POST":
        form = TipoCobroForm(request.POST, instance=tipo)
        if form.is_valid():
            form.save()
            return redirect("cobro_types_list")
    else:
        form = TipoCobroForm(instance=tipo)
    return render(request, "webapp/metodos_cobro_globales/edit_cobro_type.html", {"form": form, "tipo": tipo})