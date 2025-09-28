from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..decorators import role_required
from ..models import Categoria
from decimal import ROUND_DOWN, Decimal

# -------------------------------------------
# VISTAS PARA ADMINISTRACIÓN DE CATEGORÍAS (Posible vista nueva)
# -------------------------------------------

@login_required
@role_required("Administrador")
def manage_categories(request):
    """Vista para administrar categorías"""
    # Obtener todas las categorías
    categorias = Categoria.objects.all().order_by('nombre')
    
    # Calcular métricas
    total_categories = Categoria.objects.count()
    
    context = {
        "categorias": categorias,
        "total_categories": total_categories,
    }
    
    return render(request, "webapp/manage_categories.html", context)


@login_required
@role_required("Administrador")
def modify_category(request, category_id):
    """Vista para modificar una categoría"""
    try:
        categoria = Categoria.objects.get(id=category_id)
    except Categoria.DoesNotExist:
        messages.error(request, "Categoría no encontrada.")
        return redirect("manage_categories")
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        descuento = request.POST.get("descuento")
        
        try:
            # Validar datos
            if not nombre or not descuento:
                messages.error(request, "Todos los campos son obligatorios.")
                return redirect("modify_category", category_id=category_id)
            
            descuento = Decimal(descuento)
            if descuento < 0 or descuento > 100:
                messages.error(request, "El descuento debe estar entre 0 y 100.")
                return redirect("modify_category", category_id=category_id)
            
            # Validar máximo 1 decimal
            if descuento.as_tuple().exponent < -1:  # ej: -2 sería 2 decimales
                messages.error(request, "El descuento solo puede tener como máximo 1 decimal (ej: 10.5, no 10.55).")
                return redirect("modify_category", category_id=category_id)
            
            # Actualizar categoría
            categoria.nombre = nombre
            categoria.descuento = descuento / 100
            categoria.save()
            
            messages.success(request, f"Categoría '{categoria.nombre}' actualizada correctamente.")
            return redirect("manage_categories")
            
        except ValueError:
            messages.error(request, "El descuento debe ser un número válido.")
            return redirect("modify_category", category_id=category_id)
        except Exception as e:
            messages.error(request, "Error al actualizar la categoría.")
            return redirect("modify_category", category_id=category_id)
    
    context = {
        "categoria": categoria,
    }
    
    return render(request, "webapp/modify_category.html", context)


# -------------------------------------------
# VISTAS PARA ADMINISTRACIÓN DE CATEGORÍAS (Posible vista vieja)
# -------------------------------------------

def manage_categories(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        descuento_str = request.POST.get("descuento", "").strip()
        categoria_id = request.POST.get("id")  # Si existe, es edición

        # Validación básica
        try:
            descuento = float(descuento_str)
        except ValueError:
            messages.error(request, "El descuento debe ser un número válido")
            return redirect("manage_categories")

        if not (0 <= descuento <= 1):
            messages.error(request, "El descuento debe estar entre 0 y 1(decimal)")
            return redirect("manage_categories")

        # Validar que tenga máximo un decimal
        partes = str(descuento * 100).split(".")
        if len(partes) > 1 and len(partes[1]) > 1:
            messages.error(request, "El porcentaje solo puede tener un decimal")
            return redirect("manage_categories")

        if categoria_id:  # Editar
            categoria = get_object_or_404(Categoria, pk=categoria_id)
            categoria.nombre = nombre
            categoria.descuento = descuento
            categoria.save()
            messages.success(request, f"Categoría '{categoria.nombre}' actualizada")
        else:  # Crear
            Categoria.objects.create(nombre=nombre, descuento=descuento)
            messages.success(request, f"Categoría '{nombre}' creada")

        return redirect("manage_categories")

    # GET
    categorias = Categoria.objects.all()
    return render(request, "webapp/manage_categories.html", {"categorias": categorias})
