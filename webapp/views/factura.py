from django.shortcuts import render
from django.template.loader import get_template
from django.http import HttpResponse
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    HTML = None
    WEASYPRINT_AVAILABLE = False



# VISTA DE FACTURA
# Vista principal que muestra el iframe y el botón PDF
def ver_factura(request):
    # Podés recibir datos desde GET o backend
    factura_id = request.GET.get('factura_id', 1)  # un ID por defecto para pruebas
    cliente = request.GET.get('cliente', 'Juan Pérez')
    total = request.GET.get('total', '120000')
    condicion = request.GET.get('condicion', 'Contado')

    context = {
        'factura_id': factura_id,
        'cliente': cliente,
        'total': total,
        'condicion': condicion,
    }
    return render(request, 'webapp/compraventa_y_conversion/ver_factura.html', context)


# Vista que renderiza la factura dentro del iframe
def factura_view(request, factura_id):
    # Recibimos los datos por GET
    cliente = request.GET.get('cliente', 'Juan Pérez')
    condicion = request.GET.get('condicion', 'Contado')
    moneda = request.GET.get('moneda', 'PYG')
    total = request.GET.get('total', '120000')

    context = {
        'ruc': '80000001-2',
        'timbrado': '12345678',
        'inicio_vigencia': '01/01/2025',
        'fin_vigencia': '31/12/2025',
        'numero_factura': '001-001-0000001',

        'fecha_emision': '25/10/2025',
        'condicion': condicion,
        'cliente': cliente,
        'tipo_cliente': 'Física',
        'moneda': moneda,
        'direccion': 'Av. Principal 123',
        'nota_remision': '—',
        'documento': '1234567',
        'email': 'cliente@ejemplo.com',

        'detalle': [
            {'descripcion': 'Compra de dólares', 'cantidad': 1, 'precio': 120000, 'exentas': '-', 'iva5': '-', 'iva10': 120000},
        ],
        'subtotal_exentas': '-',
        'subtotal_iva5': '-',
        'subtotal_iva10': 120000,
        'total_operacion': 120000,
        'total_guaranies': 120000,
        'iva5': '-',
        'iva10': 12000,
        'iva_total': 12000,
    }

    return render(request, 'factura/factura.html', context)


# Vista para generar PDF con WeasyPrint
def factura_pdf(request, factura_id):
    cliente = request.GET.get('cliente', 'Juan Pérez')
    condicion = request.GET.get('condicion', 'Contado')
    moneda = request.GET.get('moneda', 'PYG')
    total = request.GET.get('total', '120000')

    context = {
        'ruc': '80000001-2',
        'timbrado': '12345678',
        'inicio_vigencia': '01/01/2025',
        'fin_vigencia': '31/12/2025',
        'numero_factura': '001-001-0000001',
        'fecha_emision': '25/10/2025',
        'condicion': condicion,
        'cliente': cliente,
        'tipo_cliente': 'Física',
        'moneda': moneda,
        'direccion': 'Av. Principal 123',
        'nota_remision': '—',
        'documento': '1234567',
        'email': 'cliente@ejemplo.com',
        'detalle': [
            {'descripcion': 'Compra de dólares', 'cantidad': 1, 'precio': 120000, 'exentas': '-', 'iva5': '-', 'iva10': 120000},
        ],
        'subtotal_exentas': '-',
        'subtotal_iva5': '-',
        'subtotal_iva10': 120000,
        'total_operacion': 120000,
        'total_guaranies': 120000,
        'iva5': '-',
        'iva10': 12000,
        'iva_total': 12000,
    }

    template = get_template('factura/factura.html')
    html_string = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="factura_{factura_id}.pdf"'

    if not WEASYPRINT_AVAILABLE:
        return HttpResponse(
            "Generación de PDF no disponible en este entorno. Habilitar weasyprint en Linux/WSL/Docker.",
            status=503,
            content_type='text/plain'
        )

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)
    return response



