# views.py
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from django.db.models import Sum
from django.http import HttpResponse
import csv
from webapp.forms import ReporteTransaccionesForm
from webapp.models import Transaccion
from django.db.models import Q

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
                t.ganancia
            ])
        return response

    context = {
        "form": form,
        "transacciones": transacciones,
        "ganancia_total": ganancia_total
    }
    return render(request, "webapp/reportes/transacciones.html", context)
