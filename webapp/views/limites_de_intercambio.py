from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_http_methods
from ..models import Currency, LimiteIntercambioConfig, Categoria
from django.urls import reverse
from django.template.loader import render_to_string
from decimal import ROUND_DOWN, Decimal

# ----------------------------------------------------------
# ADMINISTRAR LIMITES DE CAMBIO DE MONEDAS POR DIA Y POR MES
# ----------------------------------------------------------

# ---------- LISTA con selector de categoría (auto-carga primera) ----------
@login_required
@permission_required('webapp.view_limiteintercambioconfig', raise_exception=True)
def limites_intercambio_list(request):
    categorias = list(Categoria.objects.all().order_by('id'))
    if not categorias:
        return render(request, 'webapp/limites_intercambio/limites_intercambio.html', {
            "categorias": [],
            "categoria_seleccionada": None,
            "tabla_html": "<p>No hay categorías cargadas.</p>",
        })

    # ✅ SI HAY categoria_id EN LA URL, USAR ESA — SINO CARGAR LA PRIMERA
    cat_id = request.GET.get("categoria_id")
    if cat_id:
        categoria_sel = Categoria.objects.filter(id=cat_id).first() or categorias[0]
    else:
        categoria_sel = categorias[0]
        
    configs = (LimiteIntercambioConfig.objects
               .select_related("moneda", "categoria")
               .filter(categoria=categoria_sel)
               .order_by("moneda__code"))

    tabla_html = render_to_string(
        "webapp/limites_intercambio/_tabla_limites.html",
        {"configs": configs},
        request=request
    )

    return render(request, 'webapp/limites_intercambio/limites_intercambio.html', {
        "categorias": categorias,
        "categoria_seleccionada": categoria_sel,
        "tabla_html": tabla_html,
    })


# ---------- Parcial HTMX: recarga la tabla según categoría ----------
@login_required
@permission_required('webapp.view_limiteintercambioconfig', raise_exception=True)
@require_http_methods(["GET"])
def limites_intercambio_tabla_htmx(request):
    cat_id = request.GET.get("categoria_id")
    categoria = Categoria.objects.filter(id=cat_id).first()
    print(request.GET.get("categoria_id"))
    if not categoria:
        return render(request, "webapp/limites_intercambio/_tabla_limites.html", {
            "configs": [],
            "error": "Categoría no encontrada."
        })
    configs = (LimiteIntercambioConfig.objects
               .select_related("moneda", "categoria")
               .filter(categoria=categoria)
               .order_by("moneda__code"))

    return render(request, "webapp/limites_intercambio/_tabla_limites.html", {
        "configs": configs
    })

# ---------- EDITAR SOLO *_max* (por Config) ----------
@login_required
@permission_required('webapp.change_limiteintercambioconfig', raise_exception=True)
def limite_config_edit(request, config_id):
    config = LimiteIntercambioConfig.objects.select_related("moneda", "categoria").filter(pk=config_id).first()
    if not config:
        messages.error(request, "No se encontró la configuración de límite solicitada.")
        return redirect("limites_list")  # o cualquier vista segura

    if request.method == "POST":
        try:
            dec = int(config.moneda.decimales_cotizacion or 0)
            factor = Decimal('1').scaleb(-dec)

            limite_dia_max = Decimal(request.POST.get('limite_dia_max', '0')).quantize(factor, rounding=ROUND_DOWN)
            limite_mes_max = Decimal(request.POST.get('limite_mes_max', '0')).quantize(factor, rounding=ROUND_DOWN)

            if limite_dia_max < 0 or limite_mes_max < 0:
                messages.error(request, "Los límites no pueden ser negativos.")
                return redirect("limite_config_edit", config_id=config.id)

            config.limite_dia_max = limite_dia_max
            config.limite_mes_max = limite_mes_max
            config.save()

            messages.success(request, "Límites máximos actualizados.")
            # Volver a la lista, manteniendo la categoría seleccionada
            return redirect(f"{reverse('limites_list')}?categoria_id={config.categoria_id}")

        except Exception as e:
            messages.error(request, f"Error al guardar límites: {e}")

    return render(request, "webapp/limites_intercambio/limite_edit.html", {
        "moneda": config.moneda,
        "limite": config
    })