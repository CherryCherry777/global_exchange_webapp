from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import EntidadEditForm, EntidadForm
from ..models import Entidad

# ---------------------------------------------------------------
# CRUD y vista de las entidades para los metodos de pago y cobro
# ---------------------------------------------------------------

@login_required
def entidad_list(request):
    entidades = Entidad.objects.all().order_by("nombre")
    return render(request, "webapp/entidad_list.html", {"entidades": entidades})


@login_required
def entidad_create(request):
    if request.method == "POST":
        form = EntidadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Entidad creada correctamente")
            return redirect("entidad_list")
    else:
        form = EntidadForm()

    return render(request, "webapp/entidad_form.html", {"form": form})


@login_required
def entidad_update(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)

    if request.method == "POST":
        form = EntidadEditForm(request.POST, instance=entidad)
        if form.is_valid():
            form.save()
            messages.success(request, "Entidad actualizada correctamente")
            return redirect("entidad_list")
    else:
        form = EntidadEditForm(instance=entidad)

    return render(request, "webapp/entidad_form.html", {"form": form, "entidad": entidad})


@login_required
def entidad_toggle(request, pk):
    entidad = get_object_or_404(Entidad, pk=pk)
    entidad.activo = not entidad.activo
    entidad.save()
    messages.success(request, f"Entidad '{entidad.nombre}' actualizada correctamente")
    return redirect("entidad_list")
