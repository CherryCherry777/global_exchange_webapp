from django.db import connections
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime, timedelta
import os
from webapp.services.invoice_from_tx import generate_invoice_for_transaccion
from .constants import *
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.contenttypes.models import ContentType
from ..models import CurrencyDenomination, LimiteIntercambioCliente, MFACode, Transaccion, Tauser, Currency, Cliente, ClienteUsuario, TarjetaNacional, TarjetaInternacional, CuentaBancariaNegocio, Billetera, TipoCobro, TipoPago, CuentaBancariaCobro, BilleteraCobro, TauserCurrencyStock
from decimal import Decimal, ROUND_HALF_UP
from .payments.stripe_utils import procesar_pago_stripe
from .payments.cobros_simulados_a_clientes import cobrar_al_cliente_tarjeta_nacional, cobrar_al_cliente_billetera, validar_id_transferencia
from webapp.tasks import pagar_al_cliente_task
from django.template.loader import get_template
from django.http import HttpResponse
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    HTML = None
    WEASYPRINT_AVAILABLE = False
from collections import defaultdict
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

    # --- obtener tipos generales activos desde la base ---
    tipos_pago = list(
        TipoPago.objects.filter(activo=True)
        .order_by("-nombre")
        .values("id", "nombre")
    )

    tipos_cobro = list(
        TipoCobro.objects.filter(activo=True)
        .order_by("-nombre")
        .values("id", "nombre")
    )

    if request.method == "POST":
        # ------------------------------
        # MFA ANTES DE CONFIRMAR LA TRANSACCION
        # ------------------------------
        data = request.POST.dict()
        MFA_ENABLED = os.getenv("MFA_ENABLED", "true").lower() not in ("0", "false", "no", "off")
        # Pasos previo antes del MFA
        # Para metodos inactivos
        tipo_pago_id = data.get("medio_pago_tipo")
        
        try:
            tipo_pago_obj = TipoPago.objects.get(pk=tipo_pago_id)
            if not tipo_pago_obj.activo:
                messages.error(request, "El tipo de pago seleccionado ya no está disponible. Actualizá la página.")
                return redirect("compraventa")
        except TipoPago.DoesNotExist:
            messages.error(request, "Tipo de pago inválido.")
            return redirect("compraventa")
        
        tipo_cobro_id = data.get("medio_cobro_tipo")

        try:
            tipo_cobro_obj = TipoCobro.objects.get(pk=tipo_cobro_id)
            if not tipo_cobro_obj.activo:
                messages.error(
                    request,
                    "El tipo de cobro seleccionado ya no está disponible. Actualizá la página."
                )
                return redirect("compraventa")
        except TipoCobro.DoesNotExist:
            messages.error(request, "Tipo de cobro inválido.")
            return redirect("compraventa")
        # --- Si venimos desde el flujo de PIN, no regenerar MFA ---
        if "from_pin" in data:
            data.pop("from_pin", None)  # eliminamos la marca
            skip_mfa = True
        else:
            skip_mfa = False

        # 🔕 Si MFA está deshabilitado por variable de entorno, lo saltamos
        if not MFA_ENABLED:
            skip_mfa = True
            # inyectamos un código ficticio para entrar al bloque que ya tenés y continuar el flujo
            if "mfa_code" not in data:
                data["mfa_code"] = "SKIP"

        # === Paso 1: Generar MFA y solicitar código ===
        if MFA_ENABLED and "confirmar" in data and "mfa_code" not in data:
            MFACode.generate_for_user(request.user)
            messages.info(request, "Se envió un código de verificación a tu correo electrónico.")
            return render(request, "webapp/compraventa_y_conversion/verificar_mfa.html", {"data": data})

        # === Paso 2: Verificar código MFA ===
        if "mfa_code" in data:
            code = data.get("mfa_code")
            mfa_entry = MFACode.objects.filter(user=request.user, code=code, used=False).order_by("-created_at").first()

            if not skip_mfa and (not mfa_entry or not mfa_entry.is_valid()):
                messages.error(request, "El código de verificación no es válido o ha expirado. Intente de nuevo.")
                return render(request, "webapp/compraventa_y_conversion/verificar_mfa.html", {"data": data})

            if not skip_mfa:
                # marcar MFA como usado
                mfa_entry.used = True
                mfa_entry.save()

            # Confirmación final
            if "confirmar" in request.POST:
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
                    monto_origen = Decimal(data["monto_origen"])
                    monto_destino=Decimal(data["monto_destino"])
                    if monto_origen <= 0:
                        raise ValueError
                    if monto_destino <= 0:
                        raise ValueError
                except (TypeError, ValueError):
                    messages.error(request, "Debés ingresar un monto válido.")
                    return redirect('compraventa')
                
                # === Validar límite (venta PYG) contra saldo del CLIENTE ===
                if data.get("moneda_origen") == "PYG":

                    try:
                        limite_cli = (
                            LimiteIntercambioCliente.objects
                            .select_related("config__moneda")
                            .filter(cliente=cliente, config__moneda__code=data.get("moneda_destino"))
                            .order_by('-id')  # tomamos el último creado
                            .first()
                        )
                        if monto_destino > limite_cli.limite_dia_actual:
                            messages.error(request, f"El monto {monto_destino} supera el límite DIARIO disponible ({limite_cli.limite_dia_actual} {limite_cli.moneda.code}).")
                            return redirect("compraventa")
                        if monto_destino > limite_cli.limite_mes_actual:
                            messages.error(request, f"El monto {monto_destino} supera el límite MENSUAL disponible ({limite_cli.limite_mes_actual} {limite_cli.moneda.code}).")
                            return redirect("compraventa")

                    except LimiteIntercambioCliente.DoesNotExist:
                        messages.error(request, "No hay límites configurados para tu cuenta en esa moneda. Contactá soporte.")
                        return redirect("compraventa")
                
    #//////////////////////////////////////////////////////////////////////////////////////////////////////
    # Cobrar al cliente
    #//////////////////////////////////////////////////////////////////////////////////////////////////////

                # Obtener tipo de pago
                tipo_pago_raw = data.get("medio_pago_tipo")

                # Si el valor viene vacío o como 'undefined', lo tratamos como transferencia (cuentabancaria)
                if not tipo_pago_raw or tipo_pago_raw == "undefined":
                    tipo_pago_nombre = "cuentabancaria"  # nombre normalizado que usás internamente
                else:
                    try:
                        tipo_pago_general = TipoPago.objects.get(pk=tipo_pago_raw)
                        tipo_pago_nombre = tipo_pago_general.nombre.replace(" ", "").replace("_", "").lower()
                    except (TipoPago.DoesNotExist, ValueError):
                        messages.error(request, "Método de pago inválido.")
                        return redirect("compraventa")

                # Inicializar el estado
                estado = Transaccion.Estado.PENDIENTE
                payment_intent_id = None

                # TARJETA INTERNACIONAL
                # Pagos con Stripe (Tarjeta Internacional) se procesa inmediatamente
                if tipo_pago_nombre == "tarjetainternacional":
                    # Conseguir el id de la tarjeta generado por Stripe
                    tarjeta_internacional = TarjetaInternacional.objects.get(id=data["medio_pago"])
                    stripe_payment_method_id = tarjeta_internacional.stripe_payment_method_id

                    resultado = procesar_pago_stripe(
                        cliente_stripe_id=cliente.stripe_customer_id,
                        metodo_pago_id=stripe_payment_method_id,
                        # función que retorna el monto válido según las reglas de stripe
                        monto=monto_stripe(monto_origen, data["moneda_origen"]),
                        moneda=data["moneda_origen"],
                        descripcion=f"Compra/Venta de divisas ({data['tipo']})",
                    )

                    if not resultado.get("success"):
                        # Pago falló
                        messages.error(request, f"No se pudo procesar el pago: {resultado.get('message')}")
                        return redirect("compraventa")

                    estado = Transaccion.Estado.PAGADA
                    payment_intent_id = resultado.get("payment_intent_id")

                # TARJETA NACIONAL
                elif tipo_pago_nombre == "tarjetanacional":
                    tarjeta_nacional = TarjetaNacional.objects.get(id=data["medio_pago"])
                    # Validar que la el monto a cobrar(vista de la casa) esté en guaranies
                    if(data["moneda_origen"] == "PYG"):
                        resultado = cobrar_al_cliente_tarjeta_nacional(monto_origen, tarjeta_nacional.numero_tokenizado)
                        if not resultado.get("success"):
                            # Pago falló
                            messages.error(request, f"No se pudo procesar el pago: {resultado.get('message')}")
                            return redirect("compraventa")
                        
                        estado = Transaccion.Estado.PAGADA
                    else:
                        messages.error(request, f"No se puede seleccionar una tarjeta como medio de cobro")
                        return redirect("compraventa")

                # BILLETERA    
                elif tipo_pago_nombre == "billetera":
                    billetera = Billetera.objects.get(id=data["medio_pago"])
                    pin = request.POST.get("pin")  # Puede venir vacío si es la primera vez
                    cancelar = request.POST.get("cancelar")

                    if cancelar:
                        messages.info(request, "El pago con billetera fue cancelado.")
                        return redirect("compraventa")

                    resultado = cobrar_al_cliente_billetera(billetera.numero_celular, pin)

                    if resultado.get("require_pin"):
                        # Renderiza el formulario para ingresar o reintentar el PIN
                        return render(
                            request,
                            "webapp/compraventa_y_conversion/ingresar_pin.html",
                            {
                                "numero_celular": billetera.numero_celular,
                                "data": data,
                                "mensaje": resultado.get("message"),
                                "allow_retry": resultado.get("allow_retry", True),
                            },
                        )

                    if not resultado.get("success"):
                        messages.error(request, f"No se pudo procesar el pago: {resultado.get('message')}")
                        return redirect("compraventa")

                    estado = Transaccion.Estado.PAGADA

                # TRANSFERENCIA    
                elif tipo_pago_nombre == "cuentabancaria":
                    # Como no hay medio de pago seleccionado, prevenimos errores
                    try:
                        cuenta_defecto = CuentaBancariaNegocio.objects.first()
                        if not cuenta_defecto:
                            raise Exception("No existe ninguna cuenta bancaria de negocio configurada.")

                        data["medio_pago"] = cuenta_defecto.id
                        data["medio_pago_contenttype"] = ContentType.objects.get_for_model(CuentaBancariaNegocio).id
                        data["medio_pago_tipo"] = TipoPago.objects.get(nombre__iexact="Cuenta Bancaria").pk

                    except Exception as e:
                        messages.error(request, f"No se pudo vincular la cuenta bancaria del negocio: {e}")
                        return redirect("compraventa")
                    
                # TAUSER
                elif tipo_pago_nombre == "tauser":
                    print("")

    #//////////////////////////////////////////////////////////////////////////////////////////////////////
    # Pagar al cliente
    #//////////////////////////////////////////////////////////////////////////////////////////////////////

                # --- Guardar transacción ---
                transaccion = guardar_transaccion(cliente, request.user, data, estado, payment_intent_id)
                

                # Obtener tipo de cobro
                try:
                    tipo_cobro_general = TipoCobro.objects.get(id=data["medio_cobro_tipo"])
                    tipo_cobro_nombre = tipo_cobro_general.nombre.replace(" ", "").replace("_", "").lower()
                except TipoPago.DoesNotExist:
                    messages.error(request, "Método de pago inválido.")
                    return redirect("compraventa")

                # --- Pago al cliente en background ---
                if tipo_cobro_nombre != "tauser" and tipo_pago_nombre != "tauser":
                    pagar_al_cliente_task.delay(transaccion.id)

                if estado == Transaccion.Estado.PAGADA:
                    try:
                        if os.getenv("GENERAR_FACTURA"):
                            result = generate_invoice_for_transaccion(transaccion)
                        # Si preferís async:
                        # generate_invoice_task.delay(transaccion.id)
                        # messages.success(request, f"Factura emitida. Nro {result['dNumDoc']} (DE {result['de_id']}).")
                    except Exception as e:
                        messages.warning(request, f"La transacción se registró, pero falló la emisión de la factura: {e}")
                        with open("error.txt", "a") as f: f.write(f"[{datetime.now()}] {type(e).__name__}: {e}\n")

                # limpiar la sesión
                messages.success(request, "Transacción registrada.")
                return redirect("transaccion_list")

    for tipo in tipos_pago:
        nombre_normalizado = tipo["nombre"].replace(" ", "").replace("_", "").lower()
        if nombre_normalizado == "cuentabancaria":
            tipo["nombre"] = "Transferencia"""

    # Obtener la categoría del cliente
    categoria_cliente = cliente.categoria

    limites = LimiteIntercambioCliente.objects.select_related("config__moneda") \
        .filter(cliente=cliente) \
        .values(
            "config__moneda__code",
            "limite_dia_actual",
            "limite_mes_actual"
        )

    limites_dict = {
        item["config__moneda__code"]: {
            "dia": float(item["limite_dia_actual"]),
            "mes": float(item["limite_mes_actual"]),
        }
        for item in limites
    }

    # Obtener los datos de la cuenta del negocio para recibir transferencias
    cuenta_negocio = CuentaBancariaNegocio.objects.first()

    ct_tauser = ContentType.objects.get_for_model(Tauser)

    context = {
        "tipos_pago": tipos_pago,
        "tipos_cobro": tipos_cobro,
        "categoria_cliente": categoria_cliente,
        "cuenta_negocio": cuenta_negocio,
        "limites_intercambio": json.dumps(limites_dict, cls=DjangoJSONEncoder),
        "ct_tauser": ct_tauser,
    }

    return render(request, "webapp/compraventa_y_conversion/compraventa.html", context)


def get_metodos_pago_cobro(request):
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        return JsonResponse({"metodo_pago": [], "metodo_cobro": []})

    moneda_pago = request.GET.get("from")
    moneda_cobro = request.GET.get("to")

    tauser_stock = get_tauser_stock_dict()

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
            "content_type_id": ct_tauser.id,
            "stock": tauser_stock.get(t.id, {})
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
            "content_type_id": ct_tauser.id,
            "stock": tauser_stock.get(t.id, {})
        })

    return JsonResponse({"metodo_pago": metodo_pago, "metodo_cobro": metodo_cobro})


def get_tauser_stock_dict():
    data = defaultdict(lambda: defaultdict(list))

    stocks = (
        TauserCurrencyStock.objects
        .select_related("tauser", "currency", "denomination")
        .filter(tauser__activo=True, quantity__gt=0)
        .order_by("tauser_id", "currency_id", "-denomination__value")
    )

    for s in stocks:
        data[s.tauser_id][s.currency.code].append({
            "value": float(s.denomination.value),
            "quantity": s.quantity
        })

    return data


# ----------------------------------
# Vistas de historial de transacción
# ----------------------------------

def transaccion_list(request):
    """
    Muestra el historial de transacciones del cliente actual.
    Si alguna transacción tiene un medio de pago del tipo CuentaBancariaNegocio,
    se marcará con una propiedad adicional 'es_pago_cuenta_bancaria' para usar en el template.
    """
    cliente_id = request.session.get("cliente_id")
    if not cliente_id:
        messages.error(request, "No hay cliente seleccionado")
        return redirect("change_client")

    transacciones = (
        Transaccion.objects.select_related(
            "cliente", "usuario", "moneda_origen", "moneda_destino", "factura_asociada"
        )
        .filter(cliente_id=cliente_id)
        .order_by("-fecha_creacion")
    )

    # 🔹 Agregamos un atributo dinámico para cada transacción
    for t in transacciones:
        t.es_pago_cuenta_bancaria = isinstance(t.medio_pago, CuentaBancariaNegocio)

    context = {"transacciones": transacciones}
    return render(request, "webapp/compraventa_y_conversion/historial_transacciones.html", context)


@login_required
def ingresar_idTransferencia(request, transaccion_id: int):
    """
    Permite al usuario ingresar el ID de referencia de una transferencia.
    Valida el ID y, si es correcto, marca la transacción como PAGADA,
    registrando también la fecha de pago y dejando que se actualice
    la fecha_actualizacion automáticamente.
    """
    transaccion = get_object_or_404(Transaccion, pk=transaccion_id)

    if transaccion.estado == Transaccion.Estado.PENDIENTE:
        tiempo_limite = transaccion.fecha_creacion + timedelta(minutes=2)
        if timezone.now() > tiempo_limite:
            transaccion.estado = Transaccion.Estado.CANCELADA
            transaccion.save(update_fields=["estado"])
            messages.error(request, "Esta transacción expiró automáticamente.")
            return redirect("transaccion_list")

    if request.method == "POST":
        id_ingresado = request.POST.get("id_transferencia", "").strip()

        if not id_ingresado:
            messages.error(request, "Debes ingresar un ID de transferencia válido.")
            return render(
                request,
                "webapp/compraventa_y_conversion/ingresar_idTransferencia.html",
                {"transaccion": transaccion},
            )

        # ✅ Validar el ID ingresado
        resultado = validar_id_transferencia(id_ingresado)

        if not resultado.get("success"):
            messages.error(request, f"No se pudo validar la transferencia: {resultado.get('message')}")
            return render(
                request,
                "webapp/compraventa_y_conversion/ingresar_idTransferencia.html",
                {"transaccion": transaccion},
            )

        # ✅ Si pasa la validación, actualizar transacción
        transaccion.id_transferencia = id_ingresado
        transaccion.estado = Transaccion.Estado.PAGADA
        transaccion.fecha_pago = timezone.now().date()  # registra la fecha de pago (solo día)
        transaccion.save(update_fields=["id_transferencia", "estado", "fecha_pago", "fecha_actualizacion"])

        messages.success(
            request,
            "Transferencia validada correctamente. "
            "La transacción fue marcada como PAGADA y se registró la fecha de pago."
        )
        return redirect("transaccion_list")

    return render(
        request,
        "webapp/compraventa_y_conversion/ingresar_idTransferencia.html",
        {"transaccion": transaccion},
    )


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

        # ✅ Siempre devolver venta/compra sin decimales (PYG siempre)
        venta = venta.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        compra = compra.quantize(Decimal("1"), rounding=ROUND_HALF_UP)

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


