from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.contenttypes.models import ContentType
from ..models import CuentaBancaria, Transaccion, Tauser, Currency, Cliente, ClienteUsuario, TarjetaNacional, TarjetaInternacional, Billetera, TipoCobro, TipoPago, CuentaBancariaCobro, BilleteraCobro
from decimal import Decimal
from .payments.stripe_utils import procesar_pago_stripe
from webapp.tasks import pagar_al_cliente_task

# ----------------------
# Vistas de compraventa
# ----------------------

def guardar_transaccion(cliente: Cliente, usuario, data: dict, estado: str, payment_intent_id = None) -> Transaccion:
    """
    Crea y guarda una transacción con el estado indicado.
    """
    transaccion = Transaccion(
        cliente=cliente,
        usuario=usuario,
        tipo=data["tipo"],
        estado=estado,
        moneda_origen=Currency.objects.get(code=data["moneda_origen"]),
        moneda_destino=Currency.objects.get(code=data["moneda_destino"]),
        tasa_cambio=Decimal(data["tasa_cambio"]),
        monto_origen=Decimal(data["monto_origen"]),
        monto_destino=Decimal(data["monto_destino"]),
        medio_pago_type=ContentType.objects.get_for_id(data["medio_pago_contenttype"]),
        medio_pago_id=data["medio_pago"],
        medio_cobro_type=ContentType.objects.get_for_id(data["medio_cobro_contenttype"]),
        medio_cobro_id=data["medio_cobro"],
        stripe_payment_intent_id=payment_intent_id
    )
    transaccion.save()
    return transaccion


MONEDAS_SIN_DECIMALES = {"PYG", "CLP", "JPY"}  # agregar otras si aplica

def monto_stripe(monto_origen: Decimal, moneda: str) -> int:
    """
    Devuelve el monto en la unidad mínima que Stripe acepta
    según la moneda.

    Args:
        monto_origen: monto en unidades normales (Decimal o float)
        moneda: código de moneda, ej. 'PYG', 'USD'

    Returns:
        int: monto listo para enviar a Stripe
    """
    moneda = moneda.upper()
    if moneda in MONEDAS_SIN_DECIMALES:
        # Para monedas sin decimales, se envía entero
        return int(monto_origen)
    else:
        # Para monedas con decimales, se envía en centavos
        return int(monto_origen * 100)


def compraventa_view(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        # Agregar mensaje de error
        messages.error(request, "No hay cliente seleccionado")
        # Redirigir a la página change_client
        return redirect("change_client") 

    cliente = get_object_or_404(Cliente, id=cliente_id)

    # --- obtener tipos generales desde la base ---
    tipos_pago = list(TipoPago.objects.order_by("-nombre").values("id", "nombre"))
    tipos_cobro = list(TipoCobro.objects.order_by("-nombre").values("id", "nombre"))

    if request.method == "POST":
        # Confirmación final
        if "confirmar" in request.POST:
            data = request.POST.dict()  # todos los inputs del wizard
            if not data:
                messages.error(request, "No se recibieron datos del formulario. Intenta nuevamente.")
                return redirect("compraventa")

            # --- Validar tipo de transacción ---
            tipo = data.get("tipo")
            if tipo not in Transaccion.Tipo.values:
                messages.error(request, f"Tipo de transacción inválido: {tipo}")
                return redirect("compraventa")
            
            # Validación del monto
            try:
                monto_origen = float(data["monto_origen"])
                monto_destino=float(data["monto_destino"])
                if monto_origen <= 0:
                    raise ValueError
                if monto_destino <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                messages.error(request, "Debés ingresar un monto válido.")
                return redirect('compraventa')
            
            #////////////////////////////////////////////////
            # Cobrar al cliente
            #////////////////////////////////////////////////

            # Obtener tipo de pago
            try:
                tipo_pago_general = TipoPago.objects.get(pk=data["medio_pago_tipo"])
                tipo_pago_nombre = tipo_pago_general.nombre.replace(" ", "").replace("_", "").lower()
                print(tipo_pago_general)
            except TipoPago.DoesNotExist:
                messages.error(request, "Método de pago inválido.")
                return redirect("compraventa")

            # Inicializar el estado
            estado = Transaccion.Estado.PENDIENTE
            payment_intent_id = None

            # Pagos con Stripe (Tarjeta Internacional) se procesa inmediatamente
            if tipo_pago_nombre == "tarjetainternacional":
                # Conseguir el id de la tarjeta generado por Stripe
                tarjeta_internacional = TarjetaInternacional.objects.get(id=data["medio_pago"])
                stripe_payment_method_id = tarjeta_internacional.stripe_payment_method_id

                resultado = procesar_pago_stripe(
                    cliente_stripe_id=cliente.stripe_customer_id,
                    metodo_pago_id=stripe_payment_method_id,
                    monto=monto_stripe(monto_origen, data["moneda_origen"]),
                    moneda=data["moneda_origen"],
                    descripcion=f"Compra/Venta de divisas ({data['tipo']})",
                )

                if not resultado.get("success"):
                    # Pago falló: se renderiza el mismo formulario con mensaje y datos precargados
                    messages.error(request, f"No se pudo procesar el pago: {resultado.get('message')}")
                    return render(
                        request,
                        "webapp/compraventa_y_conversion/compraventa.html",
                        {
                            "tipos_pago": tipos_pago,
                            "tipos_cobro": tipos_cobro,
                            "categoria_cliente": cliente.categoria,
                            "form_data": data,  # esto sirve para rellenar los campos
                        }
                    )

                estado = Transaccion.Estado.PAGADA
                payment_intent_id = resultado.get("payment_intent_id")

            elif tipo_pago_nombre == "tarjetanacional":
                if(data["moneda_destino"] == "PYG"):
                    print("")
            elif tipo_pago_nombre == "cuentabancaria":
                print("")
            elif tipo_pago_nombre == "billetera":
                print("")
            elif tipo_pago_nombre == "tauser":
                print("")

            #////////////////////////////////////////////////
            # Pagar al cliente
            #////////////////////////////////////////////////

            # Obtener tipo de cobro
            try:
                tipo_cobro_general = TipoCobro.objects.get(id=data["medio_cobro_tipo"])
                tipo_cobro_nombre = tipo_cobro_general.nombre.replace(" ", "").replace("_", "").lower()
            except TipoPago.DoesNotExist:
                messages.error(request, "Método de pago inválido.")
                return redirect("compraventa")

            # --- Guardar transacción ---
            transaccion = guardar_transaccion(cliente, request.user, data, estado, payment_intent_id)

            # --- Pago al cliente en background ---
            if tipo_cobro_nombre != "tauser":
                pagar_al_cliente_task.delay(transaccion.id)

            # limpiar la sesión
            messages.success(request, "Transacción registrada.")
            return redirect("transaccion_list")

    for tipo in tipos_pago:
        nombre_normalizado = tipo["nombre"].replace(" ", "").replace("_", "").lower()
        if nombre_normalizado == "cuentabancaria":
            tipo["nombre"] = "Transferencia"""

    # Obtener la categoría del cliente
    categoria_cliente = cliente.categoria

    context = {
        "tipos_pago": tipos_pago,
        "tipos_cobro": tipos_cobro,
        "categoria_cliente": categoria_cliente,
    }

    return render(request, "webapp/compraventa_y_conversion/compraventa.html", context)


def get_metodos_pago_cobro(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"metodo_pago": [], "metodo_cobro": []})

    moneda_pago = request.GET.get("from")
    moneda_cobro = request.GET.get("to")

    # ---------------- ContentTypes ----------------
    ct_tarjetaNacional = ContentType.objects.get_for_model(TarjetaNacional)
    ct_tarjetaInternacional = ContentType.objects.get_for_model(TarjetaInternacional)
    ct_billetera = ContentType.objects.get_for_model(Billetera)
    ct_tauser = ContentType.objects.get_for_model(Tauser)
    ct_transferencia_cobro = ContentType.objects.get_for_model(CuentaBancariaCobro)
    ct_billetera_cobro = ContentType.objects.get_for_model(BilleteraCobro)

    # ---------------- Métodos de Pago ----------------
    metodo_pago = []

    tarjetasNacionales = TarjetaNacional.objects.filter(
        medio_pago__cliente__id=cliente_id, medio_pago__activo=True
    ).select_related("medio_pago__tipo_pago", "entidad")
    for t in tarjetasNacionales:
        if moneda_pago and t.medio_pago.moneda.code != moneda_pago:
            continue
        metodo_pago.append({
            "id": t.id,
            "tipo": "tarjeta_nacional",
            "nombre": f"{t.medio_pago.nombre} ****{t.ultimos_digitos}",
            "tipo_general_id": t.medio_pago.tipo_pago_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "content_type_id": ct_tarjetaNacional.id,
            "moneda_code": t.medio_pago.moneda.code
        })

    # 🔹 Tarjetas Internacionales
    tarjetas_internacionales = (
        TarjetaInternacional.objects
        .filter(medio_pago__cliente_id=cliente_id, medio_pago__activo=True)
        .select_related("medio_pago__tipo_pago")
    )
    for t in tarjetas_internacionales:
        metodo_pago.append({
            "id": t.id,
            "tipo": "tarjeta_internacional",
            "nombre": f"{t.medio_pago.nombre} ****{t.ultimos_digitos}",
            "tipo_general_id": t.medio_pago.tipo_pago_id,
            "moneda_code": getattr(t.medio_pago.moneda, "code", None),
            "content_type_id": ct_tarjetaInternacional.id,
        })

    
    billeteras = Billetera.objects.filter(
        medio_pago__cliente__id=cliente_id, medio_pago__activo=True
    ).select_related("medio_pago__tipo_pago", "entidad")
    for t in billeteras:
        if moneda_pago and t.medio_pago.moneda.code != moneda_pago:
            continue
        metodo_pago.append({
            "id": t.id,
            "tipo": "billetera",
            "nombre": f"{t.medio_pago.nombre} ({t.entidad.nombre}) {t.numero_celular}" if t.entidad else f"{t.nombre}",
            "tipo_general_id": t.medio_pago.tipo_pago_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_pago.moneda.code,
            "content_type_id": ct_billetera.id
        })

    tausers = Tauser.objects.filter(activo=True)
    for t in tausers:
        metodo_pago.append({
            "id": t.id,
            "tipo": t.tipo,
            "nombre": f"{t.nombre} ({t.ubicacion})",
            "ubicacion": t.ubicacion,
            "tipo_general_id": t.tipo_pago.id,
            "moneda_code": None,
            "content_type_id": ct_tauser.id
        })

    # ---------------- Métodos de Cobro ----------------
    metodo_cobro = []

    transferencias = CuentaBancariaCobro.objects.filter(
        medio_cobro__cliente__id=cliente_id, medio_cobro__activo=True
    ).select_related("medio_cobro__tipo_cobro", "entidad")
    for t in transferencias:
        if moneda_cobro and t.medio_cobro.moneda.code != moneda_cobro:
            continue
        metodo_cobro.append({
            "id": t.id,
            "tipo": "transferencia",
            "nombre": f"{t.medio_cobro.nombre} ({t.entidad.nombre}) {t.numero_cuenta}" if t.entidad else "Transferencia",
            "numero_cuenta": t.numero_cuenta,
            "tipo_general_id": t.medio_cobro.tipo_cobro_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_cobro.moneda.code,
            "content_type_id": ct_transferencia_cobro.id
        })

    billeteras = BilleteraCobro.objects.filter(
        medio_cobro__cliente__id=cliente_id, medio_cobro__activo=True
    ).select_related("medio_cobro__tipo_cobro", "entidad")
    for t in billeteras:
        if moneda_cobro and t.medio_cobro.moneda.code != moneda_cobro:
            continue
        metodo_cobro.append({
            "id": t.id,
            "tipo": "billetera",
            "nombre": f"{t.medio_cobro.nombre} ({t.entidad.nombre}) {t.numero_celular}" if t.entidad else f"{t.nombre}",
            "tipo_general_id": t.medio_cobro.tipo_cobro_id,
            "entidad": {"nombre": t.entidad.nombre} if t.entidad else None,
            "moneda_code": t.medio_cobro.moneda.code,
            "content_type_id": ct_billetera_cobro.id
        })

    tausers = Tauser.objects.filter(activo=True)
    for t in tausers:
        metodo_cobro.append({
            "id": t.id,
            "tipo": t.tipo,
            "nombre": f"{t.nombre} ({t.ubicacion})",
            "ubicacion": t.ubicacion,
            "tipo_general_id": t.tipo_cobro.id,
            "moneda_code": None,
            "content_type_id": ct_tauser.id
        })

    return JsonResponse({"metodo_pago": metodo_pago, "metodo_cobro": metodo_cobro})


def transaccion_list(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No hay cliente seleccionado")
        return redirect("change_client")  # O la vista que corresponda

    transacciones = Transaccion.objects.select_related(
        "cliente", "usuario", "moneda_origen", "moneda_destino", "factura_asociada"
    ).filter(cliente_id=cliente_id)  # Filtramos por el cliente de la sesión

    return render(request, "webapp/compraventa_y_conversion/historial_transacciones.html", {"transacciones": transacciones})


# ----------------------
# Vistas de conversión
# ----------------------

@require_GET
def api_active_currencies(request):
    user = request.user
    descuentoCategoria = Decimal('0')  # Por defecto para invitados

    if user.is_authenticated:
        try:
            # Obtener cliente asociado al usuario
            cliente_id = request.session.get("cliente_id")
            cliente_usuario = None
            if cliente_id:
                cliente_usuario = ClienteUsuario.objects.filter(
                    usuario=user,
                    cliente_id=cliente_id
                ).select_related("cliente__categoria").first()
            else:
                descuentoCategoria = Decimal('0')

            if cliente_usuario and cliente_usuario.cliente.categoria:
                descuentoCategoria = cliente_usuario.cliente.categoria.descuento or Decimal('0')
        except Exception:
            descuentoCategoria = Decimal('0')

    # Intentar obtener IDs de método de pago/cobro
    tipo_metodo_pago_id = request.GET.get("tipo_metodo_pago_id")
    tipo_metodo_cobro_id = request.GET.get("tipo_metodo_cobro_id")

    metodo_pago = None
    metodo_cobro = None
    if tipo_metodo_pago_id:
        try:
            metodo_pago = TipoPago.objects.get(id=tipo_metodo_pago_id, activo=True)
        except TipoPago.DoesNotExist:
            metodo_pago = None
    if tipo_metodo_cobro_id:
        try:
            metodo_cobro = TipoCobro.objects.get(id=tipo_metodo_cobro_id, activo=True)
        except TipoCobro.DoesNotExist:
            metodo_cobro = None

    qs = Currency.objects.filter(is_active=True)
    items = []

    for c in qs:
        base = Decimal(c.base_price)
        com_venta = Decimal(c.comision_venta)
        com_compra = Decimal(c.comision_compra)

        # Aplicar fórmulas según descuento del cliente
        venta = base + (com_venta * (1 - descuentoCategoria))
        compra = base - (com_compra * (1 - descuentoCategoria))

        # Aplicar comisiones del método seleccionado si existen
        try:
            if metodo_pago and metodo_cobro:
                # Ajusta la venta y la compra con las comisiones
                venta = venta * (1 + Decimal(metodo_pago.comision)/100 + Decimal(metodo_cobro.comision)/100)
                compra = compra * (1 - Decimal(metodo_cobro.comision)/100 - Decimal(metodo_pago.comision)/100)
            elif metodo_pago:
                # Solo existe método de pago
                venta = venta * (1 + Decimal(metodo_pago.comision)/100)
                compra = compra * (1 - Decimal(metodo_pago.comision)/100)
                # compra queda igual o se deja como estaba
            elif metodo_cobro:
                # Solo existe método de cobro
                compra = compra * (1 - Decimal(metodo_cobro.comision)/100)
                venta = venta * (1 + Decimal(metodo_cobro.comision)/100)
                # venta queda igual o se deja como estaba
        except (AttributeError, TypeError, ValueError) as e:
            # Aquí podés decidir qué hacer si algo falla:
            # - loguear el error
            # - usar comisiones 0
            # - dejar venta/compra sin modificar
            print("Error al aplicar comisiones:", e)


        items.append({
            "code": c.code,
            "name": c.name,
            "decimals": int(c.decimales_monto or 2),
            "venta": float(venta),
            "compra": float(compra),
        })

    # Asegurar que PYG siempre exista
    if not any(x["code"] == "PYG" for x in items):
        items.append({
            "code": "PYG",
            "name": "Guaraní",
            "decimals": 0,
            "venta": 1.0,
            "compra": 1.0,
        })

    return JsonResponse({"items": items})


@login_required
@require_POST
def set_cliente_seleccionado(request):
    """
    Actualiza la variable de sesión 'cliente_id' según la selección del usuario.
    - Si se recibe un cliente_id válido, se guarda en la sesión.
    - Si no se recibe, se elimina de la sesión (pop).
    Redirige a la página anterior.
    """
    cliente_id = request.POST.get("cliente_id")
    #print(cliente_id)  # Para depuración, imprime el ID seleccionado
    if cliente_id:
        request.session["cliente_id"] = int(cliente_id)
    else:
        request.session.pop('cliente_id', None)  # Borra la sesión si no hay cliente
    return redirect(request.META.get('HTTP_REFERER', '/'))