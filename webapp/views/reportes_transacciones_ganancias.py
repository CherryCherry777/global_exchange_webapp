# views.py
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.db.models import Sum
from django.http import HttpResponse
import csv
from webapp.forms import ReporteTransaccionesForm
from webapp.models import Transaccion
from django.db.models import Q
from collections import defaultdict
from django.db.models.functions import TruncDate
from django.db.models import F, Case, When, DecimalField, ExpressionWrapper
import json
from django.core.serializers.json import DjangoJSONEncoder


@permission_required("webapp.ver_reportes")
def reporte_transacciones(request):

    transacciones = Transaccion.objects.all().select_related(
        "cliente", "usuario", "moneda_origen", "moneda_destino"
    )

    form = ReporteTransaccionesForm(request.GET or None)

    if form.is_valid():
        fecha_inicio = form.cleaned_data.get("fecha_inicio")
        fecha_fin = form.cleaned_data.get("fecha_fin")
        tipo = form.cleaned_data.get("tipo")
        estado = form.cleaned_data.get("estado")
        moneda = form.cleaned_data.get("moneda")

        if fecha_inicio:
            transacciones = transacciones.filter(fecha_creacion__date__gte=fecha_inicio)
        if fecha_fin:
            transacciones = transacciones.filter(fecha_creacion__date__lte=fecha_fin)

        if tipo:
            transacciones = transacciones.filter(tipo=tipo)
        if estado:
            transacciones = transacciones.filter(estado=estado)
        if moneda:
            transacciones = transacciones.filter(
                Q(moneda_origen=moneda) |
                Q(moneda_destino=moneda)
            )

    # Ganancia total
    ganancia_total = sum(t.ganancia_en_pyg for t in transacciones)

    # Exportación CSV
    if "export_csv" in request.GET:
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="reporte_transacciones.csv"'
        writer = csv.writer(response)
        writer.writerow([
            "ID", "Fecha", "Tipo", "Estado", "Monto Origen",
            "Monto Destino", "Moneda Origen", "Moneda Destino", "Ganancia"
        ])
        for t in transacciones:
            writer.writerow([
                t.id, t.fecha_creacion, t.tipo, t.estado,
                t.monto_origen, t.monto_destino,
                t.moneda_origen.code, t.moneda_destino.code,
                t.ganancia_en_pyg
            ])
        return response

    # --- NUEVO: AGRUPAR POR FECHA ---
    # ---------------------------
    # ANOTAR GANANCIA EN PYG EN EL ORM
    # ---------------------------
    ganancia_expr = Case(

        # ---------------------------
        # CASO 1: moneda_origen = PYG
        # ---------------------------
        When(
            moneda_origen__code="PYG",
            then=ExpressionWrapper(
                (F("monto_destino") * F("monto_base_moneda"))  # costo_real
                - (                                   # tc_venta_final
                    (
                        F("monto_base_moneda") +
                        F("comision_vta_com") -
                        (F("comision_vta_com") * (F("desc_cliente")/100)) -
                        (
                            (F("monto_base_moneda") + F("comision_vta_com")) *
                            (F("medio_cobro_porc")/100)
                        )
                    )
                ),
                output_field=DecimalField(max_digits=20, decimal_places=8)
            )
        ),

        # ---------------------------
        # CASO 2: moneda_destino = PYG
        # ---------------------------
        When(
            moneda_destino__code="PYG",
            then=ExpressionWrapper(
                (F("monto_origen") * F("monto_base_moneda"))  # costo_real
                - (                                   # tc_compra_final
                    (
                        F("monto_base_moneda") -
                        F("comision_vta_com") +
                        (F("comision_vta_com") * (F("desc_cliente")/100)) +
                        (
                            (F("monto_base_moneda") - F("comision_vta_com")) *
                            (F("medio_pago_porc")/100)
                        )
                    )
                ),
                output_field=DecimalField(max_digits=20, decimal_places=8)
            )
        ),

        default=0,
        output_field=DecimalField(max_digits=20, decimal_places=8)
    )

    # APLICAR
    transacciones = transacciones.annotate(ganancia_pyg=ganancia_expr)

    ganancias_por_fecha = (
        transacciones
        .annotate(fecha=TruncDate("fecha_creacion"))
        .values("fecha")
        .annotate(total=Sum("ganancia_pyg"))
        .order_by("fecha")
    )

    # --- NUEVO: AGRUPAR POR MONEDA ---
    ganancias_por_moneda = defaultdict(int)
    for t in transacciones:
        # contabilizamos por moneda origen y destino: depende de tu lógica de negocio
        ganancias_por_moneda[t.moneda_origen.code] += t.ganancia_en_pyg

    gpf_json = json.dumps(list(ganancias_por_fecha), cls=DjangoJSONEncoder)
    gpm_json = json.dumps(dict(ganancias_por_moneda), cls=DjangoJSONEncoder)

    context = {
        "form": form,
        "transacciones": transacciones,
        "ganancia_total": ganancia_total,
        "gpf": gpf_json,  # Para gráfico líneas
        "gpm": gpm_json, # Para gráfico barras
    }
    return render(request, "webapp/reportes/transacciones.html", context)
