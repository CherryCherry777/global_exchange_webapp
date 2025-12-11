from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_http_methods
from webapp.models import Transaccion, Tauser, TauserCurrencyStock, CurrencyDenomination
from django.db.models import Q, F
from django.db import transaction
from datetime import datetime
import os

from webapp.services.invoice_from_tx import generate_invoice_for_transaccion
from webapp.tasks import pagar_al_cliente_task
from ..decorators import role_required
from decimal import Decimal
from typing import Union

User = get_user_model()

def tauser_login(request):
    """
    Login independiente para el entorno Tauser.
    Permite autenticarse con las credenciales del CustomUser principal,
    seleccionar la sucursal (ubicación) y guardar esa información en sesión.
    No inicia sesión estándar de Django.
    """
    # 🔹 Obtenemos todas las sucursales registradas (sin duplicados)
    ubicaciones = Tauser.objects.values_list("ubicacion", flat=True).distinct()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        ubicacion = request.POST.get("ubicacion")

        # Autenticación simple sin iniciar sesión Django
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Guardamos solo variables de sesión personalizadas
            request.session["tauser_authenticated"] = True
            request.session["tauser_user_id"] = user.id
            request.session["tauser_username"] = user.username
            request.session["tauser_ubicacion"] = ubicacion

            messages.success(
                request,
                f"Sesión Tauser iniciada correctamente en la sucursal: {ubicacion}."
            )
            return redirect("tauser_home")
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")

    # 🔹 Renderiza el template con las ubicaciones disponibles
    return render(
        request,
        "webapp/tauser/tauser_login.html",
        {"ubicaciones": ubicaciones},
    )


def tauser_home(request):
    """
    Lista las transacciones vinculadas a Tausers de la ubicación seleccionada.
    Solo incluye las que no están completas, anuladas, canceladas ni con AC fallida.
    """
    ubicacion = request.session.get("tauser_ubicacion")

    if not ubicacion:
        messages.warning(request, "Debe seleccionar una ubicación para continuar.")
        return redirect("tauser_login")

    # Tipo de contenido para Tauser
    ct_tauser = ContentType.objects.get_for_model(Tauser)

    # IDs de Tausers que pertenecen a esa ubicación
    tausers_ids = list(Tauser.objects.filter(ubicacion=ubicacion).values_list("id", flat=True))

    # Si no hay Tausers registrados en esa sucursal
    if not tausers_ids:
        messages.info(request, f"No hay Tausers registrados en la ubicación {ubicacion}.")
        return render(request, "webapp/tauser/tauser_home.html", {
            "transacciones": [],
            "ubicacion": ubicacion,
        })

    # Filtrar las transacciones con Tauser en medio_pago o medio_cobro
    transacciones = (
        Transaccion.objects.select_related(
            "cliente", "usuario", "moneda_origen", "moneda_destino"
        )
        .filter(
            (
                Q(medio_pago_type=ct_tauser, medio_pago_id__in=tausers_ids)
                | Q(medio_cobro_type=ct_tauser, medio_cobro_id__in=tausers_ids)
            ),
            ~Q(
                estado__in=[
                    Transaccion.Estado.COMPLETA,
                    Transaccion.Estado.ANULADA,
                    Transaccion.Estado.CANCELADA,
                    Transaccion.Estado.AC_FALLIDA,
                ]
            ),
        )
        .order_by("-fecha_creacion")
    )

    # Añadir banderas para el template
    for t in transacciones:
        t.es_pago_tauser = t.medio_pago_type == ct_tauser and t.medio_pago_id in tausers_ids
        t.es_cobro_tauser = t.medio_cobro_type == ct_tauser and t.medio_cobro_id in tausers_ids

    return render(request, "webapp/tauser/tauser_home.html", {
        "transacciones": transacciones,
        "ubicacion": ubicacion,
    })


def tauser_pagar(request, pk):
    """
    Simula un pago del cliente al sistema (Tauser como medio de pago).
    Redirige amablemente si no se encuentra la transacción.
    """
    try:
        transaccion = Transaccion.objects.get(pk=pk)
    except Transaccion.DoesNotExist:
        messages.error(request, "La transacción no existe o ya fue eliminada.")
        return redirect(request.META.get("HTTP_REFERER", reverse("tauser_home")))

    if transaccion.estado != Transaccion.Estado.PENDIENTE:
        messages.warning(request, "Esta transacción ya fue procesada o no puede pagarse.")
        return redirect("tauser_home")

    tauser = Tauser.objects.get(id=transaccion.medio_pago_id)
    moneda = transaccion.moneda_origen
    monto = transaccion.monto_origen  # Decimal

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "cancelar":
            messages.info(request, "Operación cancelada.")
            return redirect("tauser_home")

        if accion == "confirmar":
            # ✅ Si moneda NO es PYG, registrar billetes recibidos
            if moneda.code != "PYG":
                denoms = CurrencyDenomination.objects.filter(currency=moneda)
                total: Decimal = Decimal("0")
                cantidades: dict[int, int] = {}  # d.id -> qty

                # 1️⃣ Solo calculamos total y guardamos cantidades
                for d in denoms:
                    qty = int(request.POST.get(f"denom_{d.id}", 0))
                    if qty > 0:
                        total += qty * d.value
                        cantidades[d.id] = qty

                # 2️⃣ Validar antes de tocar el stock
                if total != monto:
                    messages.error(
                        request,
                        f"Los billetes ingresados ({total}) no coinciden con el monto ({monto})."
                    )
                    return redirect(request.path)

                # 3️⃣ Ahora sí, actualizar el stock porque el total es correcto
                for d in denoms:
                    qty = cantidades.get(d.id, 0)
                    if qty > 0:
                        TauserCurrencyStock.objects.update_or_create(
                            tauser=tauser,
                            currency=moneda,
                            denomination=d,
                            defaults={"quantity": F("quantity") + qty}
                        )

            # ✅ Actualizar estado
            transaccion.estado = Transaccion.Estado.PAGADA
            transaccion.save()

            try:
                if os.getenv("GENERAR_FACTURA"):
                    result = generate_invoice_for_transaccion(transaccion)
                # Si preferís async:
                # generate_invoice_task.delay(transaccion.id)
                # messages.success(request, f"Factura emitida. Nro {result['dNumDoc']} (DE {result['de_id']}).")
            except Exception as e:
                messages.warning(request, f"La transacción se registró, pero falló la emisión de la factura: {e}")
                with open("error.txt", "a") as f: f.write(f"[{datetime.now()}] {type(e).__name__}: {e}\n")

            messages.success(request, f"Transacción #{pk} PAGADA.")

            if not isinstance(transaccion.medio_cobro, Tauser):
                pagar_al_cliente_task.delay(transaccion.id)
            else:
                reservarStock(transaccion.medio_cobro.id, transaccion.moneda_destino.code, transaccion.monto_destino)

            return redirect("tauser_home")

    # 🧠 mandar lista de denominaciones al template
    denominaciones = CurrencyDenomination.objects.filter(currency=transaccion.moneda_origen)

    return render(request, "webapp/tauser/tauser_simulador.html", {
        "transaccion": transaccion,
        "modo": "pagar",
        "denominaciones": denominaciones
    })


def tauser_cobrar(request, pk):
    """
    Simula un cobro desde el sistema hacia el cliente (Tauser como medio de cobro).
    Redirige amablemente si no se encuentra la transacción.
    """
    try:
        transaccion = Transaccion.objects.get(pk=pk)
    except Transaccion.DoesNotExist:
        messages.error(request, "La transacción no existe o ya fue eliminada.")
        return redirect(request.META.get("HTTP_REFERER", reverse("tauser_home")))

    # Validar que pueda cobrarse (estado pagada)
    if transaccion.estado != Transaccion.Estado.PAGADA:
        messages.warning(request, "Esta transacción aún no puede cobrarse.")
        return redirect("tauser_home")

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "confirmar":
            transaccion.estado = Transaccion.Estado.COMPLETA
            transaccion.save(update_fields=["estado", "fecha_actualizacion"])

            messages.success(request, f"Transacción #{pk} completada con éxito.")
            return redirect("tauser_home")
        elif accion == "cancelar":
            messages.info(request, "Operación cancelada.")
            return redirect("tauser_home")

    return render(request, "webapp/tauser/tauser_simulador.html", {
        "transaccion": transaccion,
        "modo": "cobrar"
    })


def actualizar_stock_tauser(tauser_id, currency_code, monto, operacion):
    """
    operacion: 'ingreso' (tauser recibe) o 'egreso' (tauser entrega)
    No modifica stock para PYG.
    """
    if currency_code == "PYG":
        return  # Stock infinito de Guaraníes

    monto = Decimal(monto)

    stock = (
        TauserCurrencyStock.objects
        .filter(tauser_id=tauser_id, currency__code=currency_code, quantity__gt=0)
        .select_related("currency", "denomination")
        .order_by("-denomination__value")
    )

    # ✅ ingreso: tauser recibe billetes → sumamos cantidades
    if operacion == "ingreso":
        restante = monto
        for s in stock:
            denom = Decimal(s.denomination.value)

            # ¿cuántos billetes de este valor entran?
            q = restante // denom  # Decimal // Decimal ✅

            if q > 0:
                s.quantity += int(q)
                s.save(update_fields=["quantity"])
                restante -= denom * q

            if restante <= 0:
                break
        return

    # ✅ egreso: tauser entrega billetes → restamos cantidades
    restante = monto
    for s in stock:
        denom = Decimal(s.denomination.value)
        max_units = restante // denom
        usar = min(int(max_units), s.quantity)

        if usar > 0:
            s.quantity -= usar
            print(s.quantity)
            s.save(update_fields=["quantity"])
            restante -= denom * usar

        if restante <= 0:
            break

    if restante > 0:
        raise ValueError(
            f"Stock insuficiente del Tauser {tauser_id} para {monto} {currency_code}"
        )


login_required
@role_required("Administrador")
@require_http_methods(["GET", "POST"])
def manage_tausers(request):
    tausers = Tauser.objects.filter(activo=True)

    # Caso especial: no hay Tausers todavía
    if not tausers.exists():
        messages.warning(request, "No hay Tausers registrados aún.")
        return render(request, "webapp/tauser/manage_tauser.html", {
            "tausers": [],
            "selected_tauser": None,
            "stock": [],
            "total_tausers": 0,
            "total_denominations": 0,
        })

    # Determinar Tauser seleccionado
    tauser_id = request.GET.get("tauser_id")

    # Si ID no viene o no existe, elegir el primero activo
    selected_tauser = tausers.filter(id=tauser_id).first() if tauser_id else None
    if not selected_tauser:
        selected_tauser = tausers.first()  # fallback
        # Redirigimos sin romper experiencia
        return redirect(f"{request.path}?tauser_id={selected_tauser.id}")

    # POST = actualización de stock
    if request.method == "POST":
        # Reset total
        if "reset_tauser" in request.POST:
            TauserCurrencyStock.objects.filter(tauser=selected_tauser).update(quantity=0)
            messages.success(request, "Stock del Tauser vaciado correctamente.")
            return redirect(f"{request.path}?tauser_id={selected_tauser.id}")

        # Agregar stock
        den_id = request.POST.get("denomination_id")
        qty = int(request.POST.get("add_qty", 0))

        try:
            denomination = CurrencyDenomination.objects.get(id=den_id)
        except CurrencyDenomination.DoesNotExist:
            messages.error(request, "La denominación seleccionada no existe.")
            return redirect(f"{request.path}?tauser_id={selected_tauser.id}")

        if qty > 0:
            item, created = TauserCurrencyStock.objects.get_or_create(
                tauser=selected_tauser,
                denomination=denomination,
                currency=denomination.currency,  # ✅ clave faltante
                defaults={"quantity": 0}
            )
            item.quantity += qty
            item.save()

            msg = "creados" if created else "agregados"
            messages.success(request, f"Se han {msg} {qty} billetes correctamente.")

        else:
            messages.error(request, "Debe ingresar una cantidad válida.")

        return redirect(f"{request.path}?tauser_id={selected_tauser.id}")

    # GET: mostrar stock
    stock_qs = (
        TauserCurrencyStock.objects
        .filter(tauser=selected_tauser)
        .select_related("denomination__currency")
        .order_by("-denomination__currency__code", "-denomination__value")
    )

    stock = [
        {
            "stock_id": s.id,                        # id del registro de stock (no nos sirve aquí)
            "denomination_id": s.denomination.id,   # ✅ este es el que necesitamos
            "currency": s.denomination.currency.code,
            "value": s.denomination.value,
            "quantity": s.quantity,
        }
        for s in stock_qs
    ]

    return render(request, "webapp/tauser/manage_tauser.html", {
        "tausers": tausers,
        "selected_tauser": selected_tauser,
        "stock": stock,
        "total_tausers": tausers.count(),
        "total_denominations": len(stock),
    })


def reservarStock(
    tauser_id: int,
    moneda_code: str,
    monto: Union[Decimal, float, int],
) -> None:
    """
    Descuenta del stock del Tauser el monto indicado en una moneda dada.

    - Si la moneda es PYG, no hace nada (no llevás stock en PYG).
    - Envuelve la llamada a `actualizar_stock_tauser` para centralizar la lógica.

    Parámetros:
        tauser_id: ID del Tauser (medio de cobro).
        moneda_code: Código de la moneda (por ejemplo 'USD', 'EUR').
        monto: Monto a egresar del stock del Tauser.
    """

    if moneda_code == "PYG":
        # No manejás stock de PYG en Tauser, salís silenciosamente
        return

    if not monto:
        return

    # Aseguramos Decimal si estás manejando así los montos
    if not isinstance(monto, Decimal):
        monto = Decimal(str(monto))

    actualizar_stock_tauser(
        tauser_id,
        moneda_code,
        monto,
        "egreso",   # mismo modo que usabas en la view
    )

def liberarStock(
    tauser_id: int,
    moneda_code: str,
    monto: Union[Decimal, float, int],
) -> None:
    """
    Descuenta del stock del Tauser el monto indicado en una moneda dada.

    - Si la moneda es PYG, no hace nada (no llevás stock en PYG).
    - Envuelve la llamada a `actualizar_stock_tauser` para centralizar la lógica.

    Parámetros:
        tauser_id: ID del Tauser (medio de cobro).
        moneda_code: Código de la moneda (por ejemplo 'USD', 'EUR').
        monto: Monto a egresar del stock del Tauser.
    """

    if moneda_code == "PYG":
        # No manejás stock de PYG en Tauser, salís silenciosamente
        return

    if not monto:
        return

    # Aseguramos Decimal si estás manejando así los montos
    if not isinstance(monto, Decimal):
        monto = Decimal(str(monto))

    actualizar_stock_tauser(
        tauser_id,
        moneda_code,
        monto,
        "ingreso",   # mismo modo que usabas en la view
    )